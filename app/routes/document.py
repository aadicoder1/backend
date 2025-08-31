import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.core.security import get_current_user  # function to extract user from JWT

router = APIRouter(prefix="/docs", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Save file to local storage
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Save metadata in DB
    new_doc = Document(
        filename=file.filename,
        filepath=file_location,
        uploader_id=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {"message": "File uploaded successfully", "doc_id": new_doc.id}

@router.get("/search")
def search_docs(query: str):
    # Dummy search response
    return {"results": [f"Found {query} in document1.pdf"]}
