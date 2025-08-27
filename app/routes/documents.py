from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
async def upload_doc(file: UploadFile = File(...)):
    with open(f"uploads/{file.filename}", "wb") as buffer:
        buffer.write(await file.read())
    return {"msg": "File uploaded", "filename": file.filename}

@router.get("/search")
def search_docs(query: str):
    # Dummy search response
    return {"results": [f"Found {query} in document1.pdf"]}
