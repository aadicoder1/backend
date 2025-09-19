from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.utils import get_password_hash
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserLogin ,UserResponse
from app.core.security import hash_password, verify_password

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ------------------- TOKEN CREATION -------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------- REGISTER -------------------
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = get_password_hash(user.password)

    # Create new user
    new_user = User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return UserResponse schema
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email
    )

# ------------------- LOGIN -------------------
@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == payload.username).first()
    if not db_user or not verify_password(payload.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token({"sub": str(db_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role,
    }

# ------------------- GET CURRENT USER -------------------
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

# ------------------- /me Route -------------------
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user.
    Fully robust: ensures all fields exist for UserOut.
    """
    try:
        # Build a safe dict with defaults
        user_data = {
            "id": getattr(current_user, "id", 0),
            "username": getattr(current_user, "username", "Unknown"),
            "full_name": getattr(current_user, "full_name", "Unknown"),
            "email": getattr(current_user, "email", "unknown@example.com"),
            "role": getattr(current_user, "role", "Employee"),
        }
        return user_data
    except Exception as e:
        print("ERROR in /me:", e)
        raise HTTPException(status_code=500, detail="Server error fetching user")

