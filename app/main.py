from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from openai import OpenAI
from app.models.user import User
from app.routes.auth import get_current_user
from app.database import Base, engine
from app.routes import auth, document, user  # import routers

# Create database tables (only run once)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# Include routers first (before static files!)
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

# ---------------- Summarization Feature ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/summarize/{doc_id}")
async def summarize_document(doc_id: int):
    from app.models.document import Document
    from sqlalchemy.orm import Session
    from app.database import SessionLocal

    db: Session = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": f"Summarize the following document:\n\n{text}"}
        ],
        max_completion_tokens=250  # <-- correct param name now
    )

    summary = response.choices[0].message.content
    return {"summary": summary}

# Senior roles (dashboard switcher)
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

# Serve frontend AFTER defining all API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
