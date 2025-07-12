from fastapi import APIRouter, HTTPException, Depends, Form
from app.db.mongo import db
from passlib.context import CryptContext
from app.auth.jwt_handler import create_jwt_token
from app.utils.employee_id import get_next_employee_id


router = APIRouter()
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", summary="Login user (form)")
async def login_user(
    email: str = Form("", description="Your email address", example="john@example.com"),
    password: str = Form("", description="Your password", example="password123")
):
    existing = await db.users.find_one({"email": email})
    if not existing:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    valid = password_context.verify(password, existing["password"])
    if not valid:
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_jwt_token(str(existing["_id"]), existing["role"])
    return {"access_token": token, "role": existing["role"]}
