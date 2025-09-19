from typing import Literal
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict  # Pydantic v2

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
        "HR Executive",
        "Admin"
    ]

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None

    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str
