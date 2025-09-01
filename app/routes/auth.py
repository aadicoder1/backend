from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app import schemas
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme (used for token verification)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ⚠️ Use same secret + algo everywhere
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"


# ✅ Register route
@router.post("/register", response_model=schemas.user.UserOut)
def register(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    # Check username or email exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ✅ Login route
@router.post("/login")
def login(user: schemas.user.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Use user.id as subject in JWT
    token = create_access_token({"sub": str(db_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role
    }


# ✅ Get current logged-in user from JWT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
