from fastapi import APIRouter, HTTPException, Depends, Form, Request
from fastapi.responses import HTMLResponse
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

from app.db.mongo import db
from app.auth.jwt_handler import create_jwt_token
from app.utils.send_email import send_reset_email
from app.core.config import JWT_SECRET

router = APIRouter()
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESET_SECRET = JWT_SECRET


@router.post("/login", summary="Login user (form)")
async def login_user(
    email: str = Form(""),
    password: str = Form("")
):
    user = await db.users.find_one({"email": email})
    if not user or not password_context.verify(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    employee = await db.employees.find_one({"email": email})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee details not found")

    token = create_jwt_token(employee["user_id"], user["role"])

    return {
        "access_token": token,
        "userDetails": {
            "id": str(user["_id"]),
            "userid": employee.get("user_id", ""),
            "name": employee.get("name", ""),
            "email": employee.get("email", ""),
            "department": employee.get("department", ""),
            "role": employee.get("role", ""),
            "joining_date": employee.get("joining_date", "")
        }
    }


@router.post("/request-reset", summary="Request password reset")
async def request_password_reset(email: str = Form(""), request: Request = None):
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    reset_token = jwt.encode({
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, RESET_SECRET, algorithm="HS256")

    reset_link = f"https://talenttrack-om95.onrender.com/auth/reset-password?token={reset_token}"
    send_reset_email(email, reset_link)

    return {"message": "Password reset link sent to your email"}


@router.get("/reset-password", summary="Show reset form", response_class=HTMLResponse)
async def show_reset_form(token: str):
    return f"""
    <html>
        <head>
            <title>Reset Password</title>
        </head>
        <body>
            <h2>Reset Password</h2>
            <form action="/auth/reset-password" method="post">
                <input type="hidden" name="token" value="{token}" />
                <label>New Password:</label>
                <input type="password" name="new_password" required />
                <button type="submit">Reset</button>
            </form>
        </body>
    </html>
    """


@router.post("/reset-password", summary="Reset password using token")
async def reset_password(
    token: str = Form(""),
    new_password: str = Form("")
):
    try:
        payload = jwt.decode(token, RESET_SECRET, algorithms=["HS256"])
        email = payload.get("email")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_pw = password_context.hash(new_password)
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"password": hashed_pw}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Password reset successful"}
