from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
from app.database import get_db
from app.models.document import Document
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)   # ✅ now we get logged-in user
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = Document(
        title=title,
        description=description,
        file_path=file_path,
        filename=file.filename,
        user_id=current_user.id   # ✅ save uploader
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {"msg": "Document uploaded", "id": new_doc.id, "uploaded_by": current_user.username}

# Get all documents
@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()

# Get single document
@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/search")
def search_docs(query: str):
    # Dummy search response
    return {"results": [f"Found {query} in document1.pdf"]}
