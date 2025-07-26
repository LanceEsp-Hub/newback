from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas import schemas
from app.models import models
from app.utils.utils import generate_jwt_token
from app.utils.email_utils import send_verification_email
from app.token.generate_verification_token import generate_verification_token, verify_verification_token
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register(
    user: schemas.UserCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check if the email is already registered
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        # First create notification settings with all columns set to True
        new_notification = models.Notification(
            new_messages=True,
            account_updates=True,
            pet_reminders=True,
            marketing_emails=True,
            push_notifications=True
        )
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        # Hash the password before saving it to the database
        hashed_password = pwd_context.hash(user.password)
        
        # Create new user with default 'user' role and linked notification settings
        new_user = models.User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,  # Will be verified via email
            roles="user",
            notification_id=new_notification.id  # Link to the notification settings
        )
        
        # Save the new user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate a verification token for email verification
        token = generate_verification_token(new_user.email)

        # Add the email sending task to the background queue
        background_tasks.add_task(send_verification_email, new_user.email, token)

        return new_user

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create user: {str(e)}"
        )



@router.get("/verify-email")
def verify_email(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Verify the email using the provided token"""
    try:
        # Decode and verify the token
        email = verify_verification_token(token)
        if email is None:
            return RedirectResponse(
                url="/login?verification_error=invalid_token",
                status_code=302
            )

        # Find the user by the decoded email
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return RedirectResponse(
                url="/login?verification_error=user_not_found",
                status_code=302
            )

        # Mark the user as verified
        user.is_verified = True
        db.commit()

        # Redirect to login page without query params
        return RedirectResponse(
            url="https://smart-pet-eta.vercel.app/login",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url="/login?verification_error=server_error",
            status_code=302
        )

@router.post("/login")
def login(
    user: schemas.UserLogin, 
    request: Request,  # Added to get client IP
    db: Session = Depends(get_db)
):
    """Login a user and return a JWT token"""
    
    # Get client IP address for logging
    ip_address = request.client.host if request.client else None
    
    try:
        # Look up the user by email
        db_user = db.query(models.User).filter(models.User.email == user.email).first()

        # Check if the user exists and the password is correct
        if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
            # Log failed login attempt
            db.add(models.LoginLog(
                user_id=db_user.id if db_user else None,
                email=user.email,
                ip_address=ip_address,
                status="failed",
                attempt_type="login",
                login_metadata={"error": "Invalid email or password"}
            ))
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if the user is verified
        if not db_user.is_verified:
            # Log failed login attempt (unverified email)
            db.add(models.LoginLog(
                user_id=db_user.id,
                email=user.email,
                ip_address=ip_address,
                status="failed",
                attempt_type="login",
                login_metadata={"error": "Email not verified"}
            ))
            db.commit()
            raise HTTPException(status_code=403, detail="Email not verified. Please check your email.")

        # Generate a JWT token for the user
        token = generate_jwt_token(db_user.email)

        # Log successful login
        db.add(models.LoginLog(
            user_id=db_user.id,
            email=db_user.email,
            ip_address=ip_address,
            status="success",
            attempt_type="login",
            login_metadata={"name": db_user.name}
        ))
        db.commit()

        # Return the login response with the token and user information
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "roles": db_user.roles,
            "user": {
                "email": db_user.email,
                "name": db_user.name,
            },
        }

    except Exception as e:
        # Log failed login attempt (system error)
        db.add(models.LoginLog(
            user_id=None,
            email=user.email if 'user' in locals() else "unknown",
            ip_address=ip_address,
            status="failed",
            attempt_type="login",
            login_metadata={"error": str(e)}
        ))
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )
