from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from app.database import Base, engine
from app.routes import auth, document, user  # import routers

# Create database tables (only run once)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# Include routers
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

# Serve frontend static files at /static
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

