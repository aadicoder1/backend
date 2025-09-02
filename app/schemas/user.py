from typing import Literal
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict  # v2 config

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

    # Pydantic v2:
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str
