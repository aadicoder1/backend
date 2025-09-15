# app/routes/document.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import shutil, os, uuid
from datetime import datetime

from app.database import get_db ,SessionLocal
from app.models.document import Document
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="", tags=["Documents"])

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SENIOR_ROLES = {
    "Assistant Manager",
    "Manager",
    "Deputy General Manager",
    "General Manager",
    "Addl. General Manager (Operations & Maintenance)",
    "Admin"
}



@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(""),
    department: str = Form("General"),
    access_role: str = Form("All Employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handles document upload from dashboard.html
    Only senior roles (defined in SENIOR_ROLES) can upload.
    """
    # ✅ Restrict to senior roles
    if current_user.role not in SENIOR_ROLES:
        raise HTTPException(status_code=403, detail="You are not allowed to upload documents.")

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Generate unique filename
        original_name = os.path.basename(file.filename) or "file"
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        # Ensure upload dir exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Save metadata in DB
        new_doc = Document(
            title=title or original_name,
            description=description,
            file_path=file_path,
            filename=original_name,
            user_id=current_user.id,
            department=department,
            access_role=access_role,
            uploaded_at=datetime.utcnow(),
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return JSONResponse(
            {
                "msg": "✅ Document uploaded",
                "id": new_doc.id,
                "filename": new_doc.filename,
                "title": new_doc.title,
                "uploaded_by": getattr(current_user, "username", "Unknown"),
                "download_url": f"/documents/{new_doc.id}",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/list")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "title": d.title,
            "description": getattr(d, "description", ""),
            "department": getattr(d, "department", "General"),
            "access_role": getattr(d, "access_role", "All Employees"),
            "uploaded_by": getattr(d.user, "username", "Unknown") if hasattr(d, "user") else "Unknown",
            "uploaded_at": d.uploaded_at.isoformat() if getattr(d, "uploaded_at", None) else None
        }
        for d in docs
    ]


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    return FileResponse(path=doc.file_path, filename=doc.filename)


@router.delete("/delete/{doc_id}")
def delete_document(doc_id: int, current_user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Only uploader can delete
        if doc.uploaded_by != current_user.username:
            raise HTTPException(status_code=403, detail="You are not allowed to delete this document")
        
        # Delete file from filesystem
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete record from DB
        db.delete(doc)
        db.commit()
        return {"detail": "Document deleted successfully"}
    finally:
        db.close()