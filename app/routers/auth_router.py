# #backend\app\routers\auth_router.py

# from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query  # Add Query here
# from sqlalchemy.orm import Session
# from app.database.database import get_db
# from app.schemas import schemas
# from app.models import models
# from app.utils.utils import generate_jwt_token
# from app.utils.email_utils import send_verification_email
# from app.token.generate_verification_token import generate_verification_token, verify_verification_token
# from passlib.context import CryptContext

# pwd_context = CryptContext(
#     schemes=["argon2"],
#     deprecated="auto",
# )

# router = APIRouter()

# @router.post("/register", response_model=schemas.UserResponse)
# def register(
#     user: schemas.UserCreate, 
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db), 
# ):
#     existing_user = db.query(models.User).filter(models.User.email == user.email).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     hashed_password = pwd_context.hash(user.password)
#     new_user = models.User(
#         email=user.email,
#         name=user.name,
#         hashed_password=hashed_password,
#         is_active=True,
#         roles="user"
#     )
    
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     # Generate verification token
#     token = generate_verification_token(new_user.email)

#     # ✅ Add email task to background tasks
#     background_tasks.add_task(send_verification_email, new_user.email, token)

#     return new_user

# @router.get("/verify-email")
# def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
#     """Verify the email using the token"""
    
#     email = verify_verification_token(token)  # Decode and verify token
#     if email is None:
#         raise HTTPException(status_code=400, detail="Invalid or expired token")

#     user = db.query(models.User).filter(models.User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     user.is_verified = True  # Assuming you have an `is_verified` column
#     db.commit()

#     return {"message": "Email successfully verified!"}

# @router.post("/login")
# def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
#     db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
#     if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     # Check if the user is verified
#     if not db_user.is_verified:
#         raise HTTPException(status_code=403, detail="Email not verified. Please check your email.")

#     # Generate JWT Token
#     token = generate_jwt_token(db_user.email)
    
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "user_id": db_user.id,  # Include the user's ID
#         "roles": db_user.roles,
#         "user": {  # Include additional user data (optional)
#             "email": db_user.email,
#             "name": db_user.name,
#         },
#     }


from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
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
    
    # Hash the password before saving it to the database
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        is_active=True,
        roles="user"
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


# @router.get("/verify-email")
# def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
#     """Verify the email using the provided token"""
    
#     # Decode and verify the token
#     email = verify_verification_token(token)
#     if email is None:
#         raise HTTPException(status_code=400, detail="Invalid or expired token")

#     # Find the user by the decoded email
#     user = db.query(models.User).filter(models.User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Mark the user as verified
#     user.is_verified = True
#     db.commit()

#     return {"message": "Email successfully verified!"}

@router.get("/verify-email")
def verify_email(
    token: str = Query(...),
    redirect_url: str = Query("http://localhost:3000/login"),
    db: Session = Depends(get_db)
):
    """Verify the email using the provided token and redirect to login page"""
    
    try:
        # Decode and verify the token (existing logic)
        email = verify_verification_token(token)
        if email is None:
            return RedirectResponse(
                url=f"{redirect_url}?verified=false&error=Invalid+or+expired+token",
                status_code=302
            )

        # Find the user by the decoded email
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return RedirectResponse(
                url=f"{redirect_url}?verified=false&error=User+not+found",
                status_code=302
            )

        # Mark the user as verified
        user.is_verified = True
        db.commit()

        # Redirect to login page with success message
        return RedirectResponse(
            url=f"{redirect_url}?verified=true",
            status_code=302
        )
        
    except Exception as e:
        # Handle any unexpected errors
        return RedirectResponse(
            url=f"{redirect_url}?verified=false&error={str(e).replace(' ', '+')}",
            status_code=302
        )

@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login a user and return a JWT token"""
    
    # Look up the user by email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    # Check if the user exists and the password is correct
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if the user is verified
    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please check your email.")

    # Generate a JWT token for the user
    token = generate_jwt_token(db_user.email)

    # Return the login response with the token and user information
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user.id,  # Include the user's ID
        "roles": db_user.roles,
        "user": {  # Include additional user data (optional)
            "email": db_user.email,
            "name": db_user.name,
        },
    }
