from pydantic import BaseModel, EmailStr
from typing import Literal

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["admin", "hr", "employee"]

class UserLogin(BaseModel):
    email: EmailStr
    password: str
