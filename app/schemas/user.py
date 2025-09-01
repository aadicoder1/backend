from pydantic import BaseModel, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str
    role: Literal[
        "Assistant Manager",
        "Manager",
        "Deputy General Manager",
        "General Manager",
        "Executive",
        "Junior Engineer",
        "Station Controller",
        "Apprentice",
        "Additional Section Engineer (Power & Traction)",
        "Addl. General Manager (Operations & Maintenance)",
        "Executive (Civil) – Water Transport",
        "Executive (Marine)",
        "Safety Officer",
        "Finance Officer",
        "HR Executive"
    ]

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: str
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str
