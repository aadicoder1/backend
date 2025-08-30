from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
from app.schemas import user
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.user.UserOut)
def register(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    # check if username exists
    if db.query(models.user.User).filter(models.user.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pw = hash_password(user.password)
    new_user = models.user.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: schemas.user.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.user.User).filter(models.user.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}
