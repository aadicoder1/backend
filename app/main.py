from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import auth, document, user  # import routers

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# Include routers
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(document.router, prefix="/documents", tags=["documents"])

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "KMRL SmartDocs backend is running 🚀"}
