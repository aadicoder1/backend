from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login(username: str, password: str):
    
    return {"msg": f"Logged in as {username}"}
