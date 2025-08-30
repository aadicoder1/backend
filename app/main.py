from fastapi import FastAPI
from app.database import Base, engine
from app import models  
from app.models import user
from app.routes import user 
from app.routes import auth 

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# include routes
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "KMRL SmartDocs backend is running 🚀"}