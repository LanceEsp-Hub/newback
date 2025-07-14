from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
from app.utils.utils import generate_jwt_token
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from fastapi.responses import RedirectResponse
import os
import secrets
from urllib.parse import urlencode
import json
from passlib.context import CryptContext
from datetime import datetime


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id="653397573990-u5kuooniqsce99nqo2q86qdjgi2i9rmr.apps.googleusercontent.com",
    client_secret="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",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "consent",
    }
)

@router.get("/auth/google")
async def login_google(request: Request):
    # Generate a nonce
    nonce = secrets.token_urlsafe(32)
    # Store the nonce in the session
    request.session['nonce'] = nonce
    
    # Explicitly set the redirect URI
    redirect_uri = str(request.base_url)[:-1] + request.app.url_path_for("auth_google_callback")
    
    return await oauth.google.authorize_redirect(
        request, 
        redirect_uri,
        nonce=nonce
    )

# @router.get("/auth/google/callback")
# async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
#     try:
#         # Add detailed logging
#         print("Starting Google OAuth callback")
#         print("Request URL:", request.url)
#         print("Query params:", dict(request.query_params))
        
#         try:
#             # Get the token with detailed error handling
#             token = await oauth.google.authorize_access_token(request)
#             print("Token response:", token)
#         except Exception as token_error:
#             print(f"Token error: {str(token_error)}")
#             import traceback
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Failed to get access token: {str(token_error)}"
#             )

#         if not token:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="No token returned from Google"
#             )

#         try:
#             # Get user info with detailed error handling
#             user_info = token.get('userinfo')
#             if not user_info:
#                 print("No userinfo in token, trying to fetch directly")
#                 user_info = await oauth.google.userinfo(token=token)
#                 print("Userinfo response:", user_info)
#         except Exception as userinfo_error:
#             print(f"Userinfo error: {str(userinfo_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Failed to get user info: {str(userinfo_error)}"
#             )

#         if not user_info:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Could not retrieve user info"
#             )

#         # Extract user details
#         email = user_info.get("email")
#         name = user_info.get("name")
#         picture = user_info.get("picture")
        
#         if not email:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Email not provided by Google"
#             )

#         print(f"Processing user: {email}")

#         try:
#             # Check if user exists
#             user = db.query(models.User).filter(models.User.email == email).first()

#             if not user:
#                 print(f"Creating new user for {email}")
#                 # Generate a secure random password
#                 random_password = secrets.token_urlsafe(32)
#                 hashed_password = pwd_context.hash(random_password)

#                 # Create new user with default 'user' role
#                 user = models.User(
#                     email=email,
#                     name=name,
#                     hashed_password=hashed_password,
#                     is_verified=True,
#                     is_active=True,
#                     roles="user",  # Default role for new users
#                     created_at=datetime.utcnow()  # Explicitly set created_at

#                 )
#                 db.add(user)
#                 db.commit()
#                 db.refresh(user)
#                 print(f"New user created: {user.id}")

#             # Determine if user is admin
#             is_admin = user.roles == "admin"

#         except Exception as db_error:
#             db.rollback()
#             print(f"Database error: {str(db_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"Database error: {str(db_error)}"
#             )

#         try:
#             # Generate JWT token
#             jwt_token = generate_jwt_token(email)
#             print("JWT token generated successfully")

#             # Prepare query parameters
#             query_params = {
#                 'token': jwt_token,
#                 'user_id': user.id,
#                 'user': json.dumps({
#                     'email': email,
#                     'name': name,
#                     'picture': picture
#                 }),
#                 'roles': user.roles  # Include user's role
#             }

#             # Determine redirect URL based on role
#             base_url = 'http://localhost:3000/admin_dashboard' if is_admin else 'http://localhost:3000/pet_dashboard'
#             redirect_url = f"{base_url}?{urlencode(query_params)}"
            
#             print(f"Redirecting to: {redirect_url}")
            
#             response = RedirectResponse(url=redirect_url, status_code=302)
            
#             # Set cookie as a backup authentication method
#             response.set_cookie(
#                 key="auth_token",
#                 value=jwt_token,
#                 httponly=True,
#                 secure=False,  # Set to True in production with HTTPS
#                 samesite='lax',
#                 max_age=1800  # 30 minutes
#             )
            
#             return response

#         except Exception as token_gen_error:
#             print(f"Token generation error: {str(token_gen_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"Failed to generate token: {str(token_gen_error)}"
#             )

#     except Exception as e:
#         # Catch and log any unhandled exceptions
#         print(f"Unhandled error in auth callback: {str(e)}")
#         traceback.print_exc()
        
#         # Return a more informative error URL
#         error_params = {
#             'error': 'authentication_failed',
#             'message': str(e)[:100]
#         }
#         error_url = f"http://localhost:3000/login?{urlencode(error_params)}"
#         return RedirectResponse(url=error_url, status_code=302)






































# @router.get("/auth/google/callback")
# async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
#     try:
#         # Add detailed logging
#         print("Starting Google OAuth callback")
#         print("Request URL:", request.url)
#         print("Query params:", dict(request.query_params))
        
#         try:
#             # Get the token with detailed error handling
#             token = await oauth.google.authorize_access_token(request)
#             print("Token response:", token)
#         except Exception as token_error:
#             print(f"Token error: {str(token_error)}")
#             import traceback
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Failed to get access token: {str(token_error)}"
#             )

#         if not token:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="No token returned from Google"
#             )

#         try:
#             # Get user info with detailed error handling
#             user_info = token.get('userinfo')
#             if not user_info:
#                 print("No userinfo in token, trying to fetch directly")
#                 user_info = await oauth.google.userinfo(token=token)
#                 print("Userinfo response:", user_info)
#         except Exception as userinfo_error:
#             print(f"Userinfo error: {str(userinfo_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Failed to get user info: {str(userinfo_error)}"
#             )

#         if not user_info:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Could not retrieve user info"
#             )

#         # Extract user details
#         email = user_info.get("email")
#         name = user_info.get("name")
#         picture = user_info.get("picture")
        
#         if not email:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Email not provided by Google"
#             )

#         print(f"Processing user: {email}")

#         try:
#             # Check if user exists
#             user = db.query(models.User).filter(models.User.email == email).first()

#             if not user:
#                 print(f"Creating new user for {email}")
#                 # Generate a secure random password
#                 random_password = secrets.token_urlsafe(32)
#                 hashed_password = pwd_context.hash(random_password)

#                 # First create notification settings with all columns set to True
#                 new_notification = models.Notification(
#                     new_messages=True,
#                     account_updates=True,
#                     pet_reminders=True,
#                     marketing_emails=True,
#                     push_notifications=True,
#                     created_at=datetime.utcnow()
#                 )
#                 db.add(new_notification)
#                 db.commit()
#                 db.refresh(new_notification)
#                 print(f"Created notification settings: {new_notification.id}")

#                 # Create new user with default 'user' role and linked notification settings
#                 user = models.User(
#                     email=email,
#                     name=name,
#                     hashed_password=hashed_password,
#                     is_verified=True,
#                     is_active=True,
#                     roles="user",  # Default role for new users
#                     created_at=datetime.utcnow(),  # Explicitly set created_at
#                     notification_id=new_notification.id  # Link to the notification settings
#                 )
#                 db.add(user)
#                 db.commit()
#                 db.refresh(user)
#                 print(f"New user created: {user.id} with notification_id: {user.notification_id}")

#             # Determine if user is admin
#             is_admin = user.roles == "admin"

#         except Exception as db_error:
#             db.rollback()
#             print(f"Database error: {str(db_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"Database error: {str(db_error)}"
#             )

#         try:
#             # Generate JWT token
#             jwt_token = generate_jwt_token(email)
#             print("JWT token generated successfully")

#             # Prepare query parameters
#             query_params = {
#                 'token': jwt_token,
#                 'user_id': user.id,
#                 'user': json.dumps({
#                     'email': email,
#                     'name': name,
#                     'picture': picture
#                 }),
#                 'roles': user.roles  # Include user's role
#             }

#             # Determine redirect URL based on role
#             base_url = 'http://localhost:3000/admin_dashboard' if is_admin else 'http://localhost:3000/pet_dashboard'
#             redirect_url = f"{base_url}?{urlencode(query_params)}"
            
#             print(f"Redirecting to: {redirect_url}")
            
#             response = RedirectResponse(url=redirect_url, status_code=302)
            
#             # Set cookie as a backup authentication method
#             response.set_cookie(
#                 key="auth_token",
#                 value=jwt_token,
#                 httponly=True,
#                 secure=False,  # Set to True in production with HTTPS
#                 samesite='lax',
#                 max_age=1800  # 30 minutes
#             )
            
#             return response

#         except Exception as token_gen_error:
#             print(f"Token generation error: {str(token_gen_error)}")
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"Failed to generate token: {str(token_gen_error)}"
#             )

#     except Exception as e:
#         # Catch and log any unhandled exceptions
#         print(f"Unhandled error in auth callback: {str(e)}")
#         traceback.print_exc()
        
#         # Return a more informative error URL
#         error_params = {
#             'error': 'authentication_failed',
#             'message': str(e)[:100]
#         }
#         error_url = f"http://localhost:3000/login?{urlencode(error_params)}"
#         return RedirectResponse(url=error_url, status_code=302)



@router.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Add detailed logging
        print("Starting Google OAuth callback")
        print("Request URL:", request.url)
        print("Query params:", dict(request.query_params))
        
        # Get client IP address for logging
        ip_address = request.client.host if request.client else None
        
        try:
            # Get the token with detailed error handling
            token = await oauth.google.authorize_access_token(request)
            print("Token response:", token)
        except Exception as token_error:
            print(f"Token error: {str(token_error)}")
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email="unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": str(token_error)}  # Changed to login_metadata
            ))
            db.commit()
            
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to get access token: {str(token_error)}"
            )

        if not token:
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email="unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": "No token returned"}  # Changed to login_metadata
            ))
            db.commit()
            
            raise HTTPException(
                status_code=400, 
                detail="No token returned from Google"
            )

        try:
            # Get user info with detailed error handling
            user_info = token.get('userinfo')
            if not user_info:
                print("No userinfo in token, trying to fetch directly")
                user_info = await oauth.google.userinfo(token=token)
                print("Userinfo response:", user_info)
        except Exception as userinfo_error:
            print(f"Userinfo error: {str(userinfo_error)}")
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email="unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": str(userinfo_error)}  # Changed to login_metadata
            ))
            db.commit()
            
            traceback.print_exc()
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to get user info: {str(userinfo_error)}"
            )

        if not user_info:
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email="unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": "No user info"}  # Changed to login_metadata
            ))
            db.commit()
            
            raise HTTPException(
                status_code=400, 
                detail="Could not retrieve user info"
            )

        # Extract user details
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        if not email:
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email="unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": "No email provided"}  # Changed to login_metadata
            ))
            db.commit()
            
            raise HTTPException(
                status_code=400, 
                detail="Email not provided by Google"
            )

        print(f"Processing user: {email}")

        try:
            # Check if user exists
            user = db.query(models.User).filter(models.User.email == email).first()

            if not user:
                print(f"Creating new user for {email}")
                # Generate a secure random password
                random_password = secrets.token_urlsafe(32)
                hashed_password = pwd_context.hash(random_password)

                # First create notification settings with all columns set to True
                new_notification = models.Notification(
                    new_messages=True,
                    account_updates=True,
                    pet_reminders=True,
                    marketing_emails=True,
                    push_notifications=True,
                    created_at=datetime.utcnow()
                )
                db.add(new_notification)
                db.commit()
                db.refresh(new_notification)
                print(f"Created notification settings: {new_notification.id}")

                # Create new user with default 'user' role and linked notification settings
                user = models.User(
                    email=email,
                    name=name,
                    hashed_password=hashed_password,
                    is_verified=True,
                    is_active=True,
                    roles="user",  # Default role for new users
                    created_at=datetime.utcnow(),  # Explicitly set created_at
                    notification_id=new_notification.id  # Link to the notification settings
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"New user created: {user.id} with notification_id: {user.notification_id}")

            # Log successful login attempt
            db.add(models.LoginLog(
                user_id=user.id,
                email=email,
                ip_address=ip_address,
                status="success",
                attempt_type="google",
                login_metadata={"name": name, "picture": picture}  # Changed to login_metadata
            ))
            db.commit()

            # Determine if user is admin
            is_admin = user.roles == "admin"

        except Exception as db_error:
            db.rollback()
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=None,
                email=email if email else "unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": str(db_error)}  # Changed to login_metadata
            ))
            db.commit()
            
            print(f"Database error: {str(db_error)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Database error: {str(db_error)}"
            )

        try:
            # Generate JWT token
            jwt_token = generate_jwt_token(email)
            print("JWT token generated successfully")

            # Prepare query parameters
            query_params = {
                'token': jwt_token,
                'user_id': user.id,
                'user': json.dumps({
                    'email': email,
                    'name': name,
                    'picture': picture
                }),
                'roles': user.roles  # Include user's role
            }

            # Determine redirect URL based on role
            base_url = 'http://localhost:3000/admin_dashboard' if is_admin else 'http://localhost:3000/pet_dashboard'
            redirect_url = f"{base_url}?{urlencode(query_params)}"
            
            print(f"Redirecting to: {redirect_url}")
            
            response = RedirectResponse(url=redirect_url, status_code=302)
            
            # Set cookie as a backup authentication method
            response.set_cookie(
                key="auth_token",
                value=jwt_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='lax',
                max_age=1800  # 30 minutes
            )
            
            return response

        except Exception as token_gen_error:
            # Log failed attempt
            db.add(models.LoginLog(
                user_id=user.id if 'user' in locals() else None,
                email=email if email else "unknown",
                ip_address=ip_address,
                status="failed",
                attempt_type="google",
                login_metadata={"error": str(token_gen_error)}  # Changed to login_metadata
            ))
            db.commit()
            
            print(f"Token generation error: {str(token_gen_error)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate token: {str(token_gen_error)}"
            )

    except Exception as e:
        # Log failed attempt
        if 'db' in locals():  # Only if DB connection exists
            db.add(models.LoginLog(
                user_id=user.id if 'user' in locals() else None,
                email=email if 'email' in locals() else "unknown",
                ip_address=ip_address if 'ip_address' in locals() else None,
                status="failed",
                attempt_type="google",
                login_metadata={"error": str(e)}  # Changed to login_metadata
            ))
            db.commit()
        
        # Catch and log any unhandled exceptions
        print(f"Unhandled error in auth callback: {str(e)}")
        traceback.print_exc()
        
        # Return a more informative error URL
        error_params = {
            'error': 'authentication_failed',
            'message': str(e)[:100]
        }
        error_url = f"http://localhost:3000/login?{urlencode(error_params)}"
        return RedirectResponse(url=error_url, status_code=302)
