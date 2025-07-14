from jose import JWTError, jwt
from app.core.config import SECRET_KEY

def verify_verification_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")  # The email is stored as "sub"
    except JWTError:
        return None
