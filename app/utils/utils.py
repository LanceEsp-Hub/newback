#backend\app\utils\utils.py

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


SECRET_KEY = "asdasdasdsad"  # Change this to a secure key
ALGORITHM = "HS256"

def generate_jwt_token(email: str):
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": email, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

