# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def admin_required(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Your implementation to verify admin status
    # Example:
    user = db.query(User).filter(User.email == token).first()
    if not user or "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user