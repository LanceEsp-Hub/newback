# #backend\app\auth\auth.py

# from fastapi import Depends, HTTPException, Security
# from fastapi.security import OAuth2PasswordBearer#
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from app.database.database import get_db
# from app.models.models import User
# from app.token.token import decode_access_token
# from jose import JWTError
# import requests

# # OAuth2 token scheme
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# # Password hashing
# pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# GOOGLE_CLIENT_ID = "653397573990-30qo6aca71lgldvilfhktc08n3280qhn.apps.googleusercontent.com"

# def hash_password(password: str) -> str:
#     """Hashes a password using bcrypt."""
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verifies a password against the stored hash."""
#     return pwd_context.verify(plain_password, hashed_password)

# def authenticate_google_user(google_token: str):
#     """Verify Google token and get user info using Google API."""
#     google_url = "https://www.googleapis.com/oauth2/v3/userinfo"
#     headers = {"Authorization": f"Bearer {google_token}"}

#     response = requests.get(google_url, headers=headers)
#     if response.status_code != 200:
#         raise HTTPException(status_code=401, detail="Invalid Google token")

#     google_user = response.json()

#     # Ensure the token belongs to our Google app
#     if "aud" in google_user and GOOGLE_CLIENT_ID not in google_user["aud"]:
#         raise HTTPException(status_code=401, detail="Invalid Google token audience")

#     return {
#         "email": google_user.get("email"),
#         "name": google_user.get("name"),
#         "picture": google_user.get("picture")
#     }

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     print(f"Received Token: {token}")  # Debugging line

#     credentials_exception = HTTPException(
#         status_code=401,
#         detail="Invalid authentication credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         # Check if it's a Google OAuth token (usually long JWT)
#         if "." in token and len(token.split(".")) == 3:
#             google_user = authenticate_google_user(token)
#             user = db.query(User).filter(User.email == google_user["email"]).first()
            
#             if not user:
#                 # Auto-register Google users if not found
#                 user = User(email=google_user["email"], name=google_user["name"])
#                 db.add(user)
#                 db.commit()
#                 db.refresh(user)

#             return user

#         # Otherwise, process as JWT token
#         payload = decode_access_token(token)
#         print(f"Decoded Payload: {payload}")  # Debugging line

#         if not payload or not isinstance(payload, dict):
#             raise credentials_exception

#         email = payload.get("sub")
#         if not email:
#             raise credentials_exception

#         user = db.query(User).filter(User.email == email).first()
#         if not user:
#             raise credentials_exception

#         return user

#     except JWTError as e:
#         print(f"JWT Error: {str(e)}")  # Debugging line
#         raise credentials_exception


from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database.database import get_db
from app.models.models import User
from app.token.token import decode_access_token
from jose import JWTError
import requests

# OAuth2 token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

GOOGLE_CLIENT_ID = "653397573990-30qo6aca71lgldvilfhktc08n3280qhn.apps.googleusercontent.com"

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_google_user(google_token: str):
    """Verify Google token and get user info using Google API."""
    google_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {google_token}"}

    response = requests.get(google_url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_user = response.json()

    # Ensure the token belongs to our Google app
    if "aud" in google_user and GOOGLE_CLIENT_ID not in google_user["aud"]:
        raise HTTPException(status_code=401, detail="Invalid Google token audience")

    return {
        "email": google_user.get("email"),
        "name": google_user.get("name"),
        "picture": google_user.get("picture")
    }

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"Received Token: {token}")  # Debugging line

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Check if it's a Google OAuth token (usually long JWT)
        if "." in token and len(token.split(".")) == 3:
            print("Google OAuth token detected")  # Debugging line
            google_user = authenticate_google_user(token)
            user = db.query(User).filter(User.email == google_user["email"]).first()

            if not user:
                # Auto-register Google users if not found
                user = User(email=google_user["email"], name=google_user["name"])
                db.add(user)
                db.commit()
                db.refresh(user)

            return user

        # Otherwise, process as JWT token
        print("Processing as JWT token")  # Debugging line
        payload = decode_access_token(token)
        print(f"Decoded Payload: {payload}")  # Debugging line

        if not payload or not isinstance(payload, dict):
            print("Invalid payload or payload structure")  # Debugging line
            raise credentials_exception

        email = payload.get("sub")
        if not email:
            print("Email missing in payload")  # Debugging line
            raise credentials_exception

        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found for email: {email}")  # Debugging line
            raise credentials_exception

        return user

    except JWTError as e:
        print(f"JWT Error: {str(e)}")  # Debugging line
        raise credentials_exception

