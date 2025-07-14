# # backend/app/routers/pet_dashboard_router.py
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from sqlalchemy.orm import Session
# from app.database.database import get_db
# from app.models import models
# import jwt
# from datetime import datetime, timedelta

# router = APIRouter(prefix="/api", tags=["pet_dashboard"])
# security = HTTPBearer()

# # These should match what you use in your google_auth_router
# SECRET_KEY = "asdasdasdsad"  # Replace with your actual secret key
# ALGORITHM = "HS256"

# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
#     try:
#         token = credentials.credentials
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")
        
#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid token")
        
#         user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# @router.get("/pet_dashboard")
# async def get_pet_dashboard(user: models.User = Depends(get_current_user)):
#     """
#     Returns pet dashboard data for authenticated users
#     """
#     # Add your dashboard logic here
#     return {
#         "message": "Welcome to your pet dashboard",
#         "user": {
#             "email": user.email,
#             "name": user.name,
#             "role": user.roles
#         },
#         "pets": []  # Replace with actual pet data from your database
#     }


# backend/app/routers/pet_dashboard_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
import jwt
from datetime import datetime, timedelta
import os
from typing import List
from app.auth.auth import get_current_user


router = APIRouter(prefix="/api", tags=["pet_dashboard"])
security = HTTPBearer()

# Use environment variable for security key
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "asdasdasdsad")  # Use env var, fallback for dev
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
#     try:
#         token = credentials.credentials
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

#         # Prefer user ID (sub), fallback to email for older tokens
#         user_id = payload.get("sub")
#         email = payload.get("email")

#         if user_id:
#             user = db.query(models.User).filter(models.User.id == user_id).first()
#         elif email:
#             user = db.query(models.User).filter(models.User.email == email).first()
#         else:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         return user

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# # @router.get("/pet_dashboard")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials  # Extract token from the request
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")



# async def get_pet_dashboard(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     Returns pet dashboard data for authenticated users
#     """
#     # Query pets owned by this user
#     pets = db.query(models.Pet).filter(models.Pet.owner_id == user.id).all()

#     return {
#         "message": "Welcome to your pet dashboard",
#         "user": {
#             "email": user.email,
#             "name": user.name,
#             "role": user.roles
#         },
#         "pets": [
#             {
#                 "id": pet.id,
#                 "name": pet.name,
#                 "species": pet.species,
#                 "age": pet.age,
#                 "status": pet.status
#             } for pet in pets
#         ]
#     }


# @router.get("/pet_dashboard")
# async def get_pet_dashboard(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     Returns pet dashboard data for authenticated users
#     """
#     pets = db.query(models.Pet).filter(models.Pet.user_id == user.id).all()
#     pets_data = [
#         {
#             "id": pet.id,
#             "name": pet.name,
#             "type": pet.type,
#             "gender": pet.gender,
#             "description": pet.description,
#             "date": pet.date.isoformat(),
#             "address": pet.address,
#             "status": pet.status,
#             "image": pet.image,
#         }
#         for pet in pets
#     ]
#     return {
#         "message": "Welcome to your pet dashboard",
#         "user": {
#             "email": user.email,
#             "name": user.name,
#             "role": user.roles
#         },
#         "pets": pets_data
#     }

@router.get("/pet_dashboard", response_model=dict)
def get_pet_dashboard(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Query the pets associated with the user (assuming there's a relationship between users and pets)
        pets = db.query(models.Pet).filter(models.Pet.user_id == user.id).all()
        
        if not pets:
            raise HTTPException(status_code=404, detail="No pets found for this user")

        # Return the pets data and user details
        return {"user": {"email": user.email, "name": user.name}, "pets": pets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    