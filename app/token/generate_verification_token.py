import jwt  # Ensure you are using the correct library
from datetime import datetime, timedelta
from jose import jwt, JWTError  # ✅ Correct

SECRET_KEY = "asdasdasdsad"
ALGORITHM = "HS256"

def generate_verification_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  # Correct usage
    return token

def verify_verification_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")  # The email is stored as "sub"
    except JWTError:
        return None
    
def decode_access_token(token: str):
    """Decodes a JWT token and returns the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None  # Return None if the token is invalid or expired