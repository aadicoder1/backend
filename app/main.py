from fastapi import FastAPI
from app.routes import auth, documents

app = FastAPI(title="KMRL SmartDocs")

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

@app.get("/")
def root():
    return {"msg": "KMRL SmartDocs API running 🚉"}
