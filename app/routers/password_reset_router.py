#backend\app\routers\password_reset_router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import ForgotPasswordRequest  # Import ForgotPasswordRequest here
from app.utils.email_utils import send_password_reset_email
from datetime import datetime, timedelta
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


router = APIRouter()

reset_tokens = {}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Check if the email exists in the database
    db_user = db.query(User).filter(User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Generate a reset token
    reset_token = secrets.token_urlsafe(32)
    reset_tokens[reset_token] = {
        "email": request.email,
        "expires_at": datetime.utcnow() + timedelta(hours=1),  # Token expires in 1 hour
    }

    # Send the reset email
    await send_password_reset_email(request.email, reset_token)

    return {"message": "Password reset email sent"}

@router.post("/reset-password")
async def reset_password(
    token: str = Query(..., description="The reset token"),  # Token as query parameter
    new_password: str = Query(..., description="The new password"),  # New password as query parameter
    db: Session = Depends(get_db)
):
    # Check if the token is valid
    token_data = reset_tokens.get(token)
    if not token_data or token_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Update the user's password using Argon2
    db_user = db.query(User).filter(User.email == token_data["email"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.hashed_password = pwd_context.hash(new_password)  # Hash the new password with Argon2
    db.commit()

    # Remove the token from storage
    del reset_tokens[token]

    return {"message": "Password reset successfully"}


