from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import shutil, os, uuid
from datetime import datetime
import json
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.document_access import DocumentAccess
from app.routes.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SENIOR_ROLES = {
    "Assistant Manager",
    "Manager",
    "Deputy General Manager",
    "General Manager",
    "Addl. General Manager (Operations & Maintenance)",
    "Admin",
}

# ---------------- Upload ----------------
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(""),
    department: str = Form("General"),
    access_role: str = Form("All Employees"),  # comes as JSON string
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in SENIOR_ROLES:
        raise HTTPException(status_code=403, detail="You are not allowed to upload documents.")

    try:
        roles = json.loads(access_role) if access_role else []
        if not isinstance(roles, list):
            roles = [str(roles)]
        access_role_str = ",".join(roles)  # store as comma-separated in DB
    except:
        access_role_str = str(access_role)

    original_name = os.path.basename(file.filename) or "file"
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = Document(
        title=title or original_name,
        description=description,
        file_path=file_path,
        filename=original_name,
        user_id=current_user.id,
        department=department,
        access_role=access_role_str,
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {
        "msg": "✅ Document uploaded",
        "id": new_doc.id,
        "filename": new_doc.filename,
        "title": new_doc.title,
        "uploaded_by": current_user.username,
        "access": new_doc.access_role,
        "department": new_doc.department,
        "uploaded_at": new_doc.uploaded_at.isoformat(),
        "download_url": f"/documents/{new_doc.id}",
    }


# ---------------- Grant Access ----------------
@router.post("/grant/{doc_id}")
def grant_access(
    doc_id: int,
    employee_id: int = Form(...),
    access_level: str = Form("view"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in SENIOR_ROLES:
        raise HTTPException(status_code=403, detail="Only senior roles can grant access.")

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    grant = DocumentAccess(
        doc_id=doc_id,
        user_id=employee_id,
        granted_by=current_user.id,
        access_level=access_level,
    )
    db.add(grant)
    db.commit()
    return {"msg": f"✅ Access granted to {employee.username}"}


# ---------------- List ----------------
@router.get("/list")
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role in SENIOR_ROLES:
        docs = db.query(Document).all()
    else:
        docs = (
            db.query(Document)
            .join(DocumentAccess)
            .filter(DocumentAccess.user_id == current_user.id)
            .all()
        )

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "title": d.title,
            "description": d.description or "",
            "department": d.department or "General",
            "access_role": d.access_role or "Restricted",   # ✅ fixed to match frontend
            "uploaded_by": d.user.username if d.user else "Unknown",
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ]



# ---------------- Download ----------------
@router.get("/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role not in SENIOR_ROLES:
        access = (
            db.query(DocumentAccess)
            .filter(
                DocumentAccess.doc_id == doc_id,
                DocumentAccess.user_id == current_user.id
            )
            .first()
        )
        if not access:
            raise HTTPException(status_code=403, detail="You do not have access to this document")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    return FileResponse(path=doc.file_path, filename=os.path.basename(doc.file_path))


# ---------------- Delete ----------------
@router.delete("/delete/{doc_id}")
@router.post("/delete/{doc_id}")  # fallback
def delete_document(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role not in SENIOR_ROLES and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this document")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"detail": "✅ Document deleted successfully"}


# ---------------- Notifications (Dummy) ----------------
@router.get("/notifications")
def get_notifications():
    return [
        {"message": "Welcome back!"},
        {"message": "2 documents pending review"},
        {"message": "System check passed ✅"},
    ]
