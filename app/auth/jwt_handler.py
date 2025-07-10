from datetime import datetime, timedelta
from jose import jwt
from app.core.config import JWT_SECRET

SECRET = JWT_SECRET

def create_jwt_token(user_id: str, role: str):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def decode_jwt_token(token: str):
    return jwt.decode(token, SECRET, algorithms=["HS256"])
