from fastapi import APIRouter, HTTPException, Depends, Form
from app.db.mongo import db
from passlib.context import CryptContext
from app.auth.jwt_handler import create_jwt_token

router = APIRouter()
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", summary="Register new user (form)")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = password_context.hash(password)
    user_data = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "role": role
    }

    result = await db.users.insert_one(user_data)
    return {"message": "User registered", "id": str(result.inserted_id)}

@router.post("/login", summary="Login user (form)")
async def login_user(
    email: str = Form(...),
    password: str = Form(...)
):
    existing = await db.users.find_one({"email": email})
    if not existing:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    valid = password_context.verify(password, existing["password"])
    if not valid:
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_jwt_token(str(existing["_id"]), existing["role"])
    return {"access_token": token, "role": existing["role"]}
