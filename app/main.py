# backend/app/main.py
import os
import re
import requests
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# load environment variables from .env if present
load_dotenv()

# only import OpenAI client if user provided a key (safe init)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

HF_API_KEY = os.getenv("HF_API_KEY")        # Hugging Face token (preferred for quick integration)
HF_MODEL = os.getenv("HF_MODEL", "sshleifer/distilbart-cnn-12-6")  # default HF model for summarization

from app.database import Base, engine, SessionLocal
from app.routes import auth, document, user  # import routers
from app.models.user import User
from app.routes.auth import get_current_user

# Create database tables (only run once)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# Include routers first (so routes take precedence over static files)
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(document.router, prefix="/documents", tags=["documents"])

# Enable CORS for frontend (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Utilities ----------------
def mock_summary(text: str) -> str:
    """Very small fallback summarizer: take first 2-3 sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:3]) if sentences else ""

def extract_text_from_file(file_path: str) -> str:
    """
    Try to read file as UTF-8 text; if fails, attempt PDF / DOCX extraction.
    Raises HTTPException with instructive message on failure.
    """
    # try plain text first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # fallback by extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
        except Exception as e:
            raise HTTPException(status_code=400, detail="To extract PDF text install PyPDF2: pip install PyPDF2")
        try:
            reader = PdfReader(file_path)
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

    if ext in (".docx",):
        try:
            import docx
            from docx import Document as DocxDocument
        except Exception:
            raise HTTPException(status_code=400, detail="To extract DOCX text install python-docx: pip install python-docx")
        try:
            doc = DocxDocument(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {str(e)}")

    raise HTTPException(status_code=400, detail="Unsupported file format. Supported: .txt, .pdf, .docx")

def summarize_with_hf(text: str) -> Optional[str]:
    """Call Hugging Face Inference API; return summary string or None on failure."""
    if not HF_API_KEY:
        return None

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": text,
        "parameters": {"max_length": 130, "min_length": 30},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        # network or DNS error
        return None

    if resp.status_code != 200:
        # non-200 => treat as failure (caller may fallback)
        return None

    try:
        data = resp.json()
        # HF model usually returns [{'summary_text': '...'}] for summarization models
        if isinstance(data, list) and isinstance(data[0], dict) and "summary_text" in data[0]:
            return data[0]["summary_text"]
        # some models return plain text or different schema; attempt to handle common cases
        if isinstance(data, dict) and "summary_text" in data:
            return data["summary_text"]
        if isinstance(data, list) and isinstance(data[0], str):
            return data[0]
        # otherwise return stringified response
        return str(data)
    except Exception:
        return None

def summarize_with_openai(text: str) -> Optional[str]:
    """Call OpenAI if configured; returns summary or None on error."""
    if not openai_client:
        return None
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                {"role": "user", "content": f"Summarize the following document:\n\n{text}"}
            ],
            max_completion_tokens=250
        )
        # Extract result (SDK may return nested structure)
        return response.choices[0].message.content
    except Exception as e:
        # bubble up None to let caller fallback
        return None

# ---------------- Summarization Endpoint ----------------
@app.get("/summarize/{doc_id}")
async def summarize_document(doc_id: int):
    from app.models.document import Document
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = getattr(doc, "file_path", None)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on server")

        # Extract text (supports .txt, .pdf, .docx if libs installed)
        text = extract_text_from_file(file_path)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Document contains no extractable text")

        # Try Hugging Face first (recommended for quick free-tier integration)
        hf_summary = summarize_with_hf(text)
        if hf_summary:
            return {"summary": hf_summary, "source": "huggingface"}

        # Then try OpenAI if configured
        openai_summary = summarize_with_openai(text)
        if openai_summary:
            return {"summary": openai_summary, "source": "openai"}

        # Fallback to a simple local summarizer
        fallback = mock_summary(text)
        return {"summary": fallback, "source": "fallback"}

    finally:
        db.close()

# ---------------- Dashboard & static serving ----------------
SENIOR_ROLES = {
    "Assistant Manager",
    "Manager",
    "Deputy General Manager",
    "General Manager",
    "Addl. General Manager (Operations & Maintenance)",
    "Admin"
}

@app.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role in SENIOR_ROLES:
        return FileResponse(os.path.join("frontend", "dashboard.html"))
    else:
        return FileResponse(os.path.join("frontend", "employee_dashboard.html"))

# Serve frontend AFTER defining all API routes so they are not overshadowed by static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
