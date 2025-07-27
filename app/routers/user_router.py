#backend\app\routers\user_router.py

from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks, Form, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
from datetime import datetime, timedelta
import secrets
from app.utils.email_utils import send_password_reset_email
from app.models.models import User
from supabase import create_client

from passlib.context import CryptContext
import os
import uuid
import logging
import httpx

from pathlib import Path


router = APIRouter(prefix="/api/user", tags=["users"])  # Changed tag to plural for consistency
logger = logging.getLogger(__name__)

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "profile-pictures")

print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY[:5], "...")  # Only show part for safety

# In-memory rate limiting (simple alternative)
_request_counts = {}

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase initialized successfully")
except Exception as e:
    logger.error(f"Supabase init failed: {str(e)}")
    raise RuntimeError("Supabase initialization failed") from e

# Profile Picture Uploads
UPLOAD_DIR = Path("app/uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str = "system"):
    """Helper function to create notifications"""
    notification = models.UserNotification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user_account(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account by setting is_active=False and recording deactivation time
    """
    try:
        # Find the user
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Mark account as inactive
        db_user.is_active = False
        db_user.deactivated_at = datetime.utcnow()
        db_user.email = f"deactivated_{db_user.email}"  # Simple email modification
        db_user.hashed_password = ""  # Clear password
        db_user.reset_token = None
        db_user.reset_token_expires_at = None
        
        # Commit changes
        db.commit()
        
        logger.info(f"User {user_id} deactivated at {db_user.deactivated_at}")
        return {
            "message": "Account deactivated successfully",
            "deactivated_at": db_user.deactivated_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating account: {str(e)}"
        )
# working code for the get user without supabase
# @router.get("/{user_id}")
# async def get_user(user_id: int, db: Session = Depends(get_db)):
#     try:
#         user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         return {
#             "id": user.id,
#             "name": user.name,
#             "email": user.email,
#             "profile_picture": user.profile_picture,
#             "phone_number": user.phone_number
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found")
        
        # Only add this if condition to handle profile picture
        profile_url = None
        if user.profile_picture:
            profile_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{user.profile_picture}"
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "profile_picture": profile_url,  # Now returns URL or None
            "phone_number": user.phone_number
            # ... (keep all other fields exactly as they were)
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# original working code without supabase
# @router.post("/upload-picture")
# async def upload_profile_picture(file: UploadFile = File(...)):
#     try:
#         if not file.filename:
#             raise HTTPException(status_code=400, detail="No file provided")

#         filename = f"profile_{uuid.uuid4().hex[:8]}_{file.filename}"
#         file_path = os.path.join(UPLOAD_DIR, filename)

#         # Check file size (5MB max)
#         file.file.seek(0, 2)
#         file_size = file.file.tell()
#         file.file.seek(0)
#         if file_size > 5 * 1024 * 1024:
#             raise HTTPException(status_code=400, detail="File too large (max 5MB)")

#         with open(file_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)

#         return {"filename": filename}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))






# working code for the supabase
# @router.post("/upload-picture")
# async def upload_profile_picture(file: UploadFile = File(...)):
#     try:
#         # Validate file
#         if not file.content_type or not file.content_type.startswith('image/'):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Only image files are allowed (JPEG, PNG, WEBP)"
#             )

#         # Check size (5MB max)
#         file_bytes = await file.read()
#         if len(file_bytes) > 5 * 1024 * 1024:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="File too large (max 5MB)"
#             )

#         # Generate filename
#         ext = Path(file.filename).suffix.lower()
#         valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
#         if ext not in valid_extensions:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Invalid file extension. Allowed: {', '.join(valid_extensions)}"
#             )
        
#         filename = f"user_{uuid.uuid4().hex}{ext}"

#         # Upload directly using Supabase Storage API
#         upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
#         headers = {
#             "Authorization": f"Bearer {SUPABASE_KEY}",
#             "Content-Type": file.content_type,
#             "x-upsert": "true"  # Enable overwrite if file exists
#         }

#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 upload_url,
#                 headers=headers,
#                 content=file_bytes
#             )

#         if response.status_code not in [200, 201]:
#             error_detail = response.json().get("error", {}).get("message", "Unknown error")
#             raise HTTPException(
#                 status_code=status.HTTP_502_BAD_GATEWAY,
#                 detail=f"Supabase upload failed: {error_detail}"
#             )

#         # Get public URL
#         public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"

#         return {
#             "status": "success",
#             "filename": filename,
#             "url": public_url,
#             "size": len(file_bytes)
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Upload failed: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="File upload failed"
#         )
@router.post("/upload-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 1. Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, detail="Only images allowed")

        # 2. Generate filename (same as before)
        ext = Path(file.filename).suffix.lower()
        filename = f"user_{uuid.uuid4().hex}{ext}"
        content = await file.read()

        # 3. Upload to Supabase (existing code)
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=filename,
            file=content,
            file_options={"content-type": file.content_type}
        )

        # 4. Return response (same structure as before)
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
        
        return {
            "filename": filename,  # Keep returning filename
            "url": public_url      # And URL for immediate frontend use
        }

    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.patch("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        changes = []
        
        # Basic user info updates
        if "name" in user_data and user_data["name"] != user.name:
            changes.append(f"Name updated from {user.name} to {user_data['name']}")
            user.name = user_data["name"]
        
        if "phone_number" in user_data and user_data["phone_number"] != user.phone_number:
            changes.append("Phone number updated")
            user.phone_number = user_data["phone_number"]
        
        if "profile_picture" in user_data:
            changes.append("Profile picture updated")
            user.profile_picture = user_data["profile_picture"]

        # Handle notification preferences if included in update
        if "notification_preferences" in user_data and user.notification_id:
            notification = db.query(models.Notification).filter(
                models.Notification.id == user.notification_id
            ).first()
            
            if notification:
                pref_changes = []
                pref_data = user_data["notification_preferences"]
                
                # Check each notification preference field
                for field in ["new_messages", "account_updates", 
                             "pet_reminders", "marketing_emails", 
                             "push_notifications"]:
                    if field in pref_data and getattr(notification, field) != pref_data[field]:
                        setattr(notification, field, pref_data[field])
                        pref_changes.append(field.replace('_', ' '))
                
                if pref_changes:
                    changes.append(f"Notification preferences updated: {', '.join(pref_changes)}")
                    notification.updated_at = datetime.utcnow()

        if changes:
            db.commit()
            
            # Only create notification if account updates are enabled
            if not user.notification_id or (
                user.notification_id and 
                db.query(models.Notification)
                .filter(models.Notification.id == user.notification_id)
                .first().account_updates
            ):
                create_notification(
                    db,
                    user_id,
                    "Profile Updated",
                    f"Your profile was updated: {', '.join(changes)}",
                    "account"
                )
            
            return {"message": "User updated successfully"}
        else:
            return {"message": "No changes detected"}
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# backend/app/routers/user_router.py
@router.get("/{user_id}/address")
async def get_user_address(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.address_id:
            return None  # Return None when no address exists
            
        address = db.query(models.Address).filter(models.Address.id == user.address_id).first()
        if not address:
            return None
            
        return {
            "street": address.street,
            "barangay": address.barangay,
            "city": address.city,
            "state": address.state,
            "zip_code": address.zip_code,
            "country": address.country
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.patch("/{user_id}/address", status_code=status.HTTP_200_OK)
# async def update_user_address(
#     user_id: int,
#     address_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         if not user.address_id:
#             new_address = models.Address(**address_data)
#             db.add(new_address)
#             db.commit()
#             db.refresh(new_address)
#             user.address_id = new_address.id
#             action = "created"
#         else:
#             address = db.query(models.Address).filter(models.Address.id == user.address_id).first()
#             if address:
#                 changes = []
#                 for field in ["street", "barangay", "city", "state", "zip_code", "country"]:
#                     if field in address_data and getattr(address, field) != address_data[field]:
#                         setattr(address, field, address_data[field])
#                         changes.append(field)
#                 action = "updated" if changes else "unchanged"
        
#         db.commit()
        
#         if action != "unchanged":
#             create_notification(
#                 db,
#                 user_id,
#                 "Address Updated",
#                 f"Your address was {action}",
#                 "account"
#             )
        
#         return {"message": f"Address {action} successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/address", status_code=status.HTTP_200_OK)
async def update_user_address(
    user_id: int,
    address_data: dict,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        changes = []
        action = "unchanged"
        
        if not user.address_id:
            # Create new address
            new_address = models.Address(**address_data)
            db.add(new_address)
            db.commit()
            db.refresh(new_address)
            user.address_id = new_address.id
            action = "created"
            changes = ["all address fields set"]
        else:
            # Update existing address
            address = db.query(models.Address).filter(models.Address.id == user.address_id).first()
            if address:
                field_changes = []
                for field in ["street", "barangay", "city", "state", "zip_code", "country"]:
                    if field in address_data and getattr(address, field) != address_data[field]:
                        setattr(address, field, address_data[field])
                        field_changes.append(field.replace('_', ' '))
                
                if field_changes:
                    action = "updated"
                    changes = field_changes
        
        db.commit()
        
        # Only send notification if account updates are enabled
        if action != "unchanged":
            # Check if account updates are enabled in notification preferences
            send_notification = True
            if user.notification_id:
                notification_prefs = db.query(models.Notification).filter(
                    models.Notification.id == user.notification_id
                ).first()
                send_notification = notification_prefs.account_updates if notification_prefs else True
            
            if send_notification:
                change_details = ": " + ", ".join(changes) if changes else ""
                create_notification(
                    db,
                    user_id,
                    "Address Updated",
                    f"Your address was {action}{change_details}",
                    "account"
                )
        
        return {
            "message": f"Address {action} successfully",
            "changes": changes if action != "unchanged" else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Notification Endpoints
@router.get("/{user_id}/notifications")
async def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return default settings if no notification settings exist
        if not user.notification_id:
            return {
                "new_messages": True,
                "account_updates": True,
                "pet_reminders": True,
                "marketing_emails": False,
                "push_notifications": True
            }
        
        notification = db.query(models.Notification).filter(
            models.Notification.id == user.notification_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification settings not found")
            
        return {
            "new_messages": notification.new_messages,
            "account_updates": notification.account_updates,
            "pet_reminders": notification.pet_reminders,
            "marketing_emails": notification.marketing_emails,
            "push_notifications": notification.push_notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# @router.patch("/{user_id}/notifications", status_code=status.HTTP_200_OK)
# async def update_user_notifications(
#     user_id: int,
#     notification_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         changes = []
        
#         if not user.notification_id:
#             new_notification = models.Notification(
#                 new_messages=notification_data.get("new_messages", True),
#                 account_updates=notification_data.get("account_updates", True),
#                 pet_reminders=notification_data.get("pet_reminders", True),
#                 marketing_emails=notification_data.get("marketing_emails", False),
#                 push_notifications=notification_data.get("push_notifications", True)
#             )
#             db.add(new_notification)
#             db.commit()
#             db.refresh(new_notification)
#             user.notification_id = new_notification.id
#             changes.append("Notification preferences created")
#         else:
#             notification = db.query(models.Notification).filter(
#                 models.Notification.id == user.notification_id
#             ).first()
            
#             if notification:
#                 for setting in ["new_messages", "account_updates", "pet_reminders", 
#                               "marketing_emails", "push_notifications"]:
#                     if setting in notification_data and getattr(notification, setting) != notification_data[setting]:
#                         setattr(notification, setting, notification_data[setting])
#                         changes.append(f"{setting.replace('_', ' ')} updated")
#                 notification.updated_at = datetime.utcnow()
        
#         db.commit()
        
#         if changes:
#             create_notification(
#                 db,
#                 user_id,
#                 "Notification Settings Changed",
#                 "Changes made to your notification preferences: " + ", ".join(changes),
#                 "account"
#             )
        
#         return {"message": "Notification settings updated successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}/notifications", status_code=status.HTTP_200_OK)
async def update_user_notifications(
    user_id: int,
    notification_data: dict,
    db: Session = Depends(get_db)
):
    try:
        # Validate input data
        if not notification_data:
            raise HTTPException(status_code=400, detail="No notification data provided")
        
        # Get user and validate existence
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        changes = []
        notification_settings = None
        
        # Create new notification preferences if they don't exist
        if not user.notification_id:
            new_notification = models.Notification(
                new_messages=notification_data.get("new_messages", True),
                account_updates=notification_data.get("account_updates", True),
                pet_reminders=notification_data.get("pet_reminders", True),
                marketing_emails=notification_data.get("marketing_emails", False),
                push_notifications=notification_data.get("push_notifications", True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)
            user.notification_id = new_notification.id
            changes.append("Initial notification preferences set")
            notification_settings = new_notification
        else:
            # Update existing notification preferences
            notification_settings = db.query(models.Notification).filter(
                models.Notification.id == user.notification_id
            ).first()
            
            if notification_settings:
                valid_settings = ["new_messages", "account_updates", "pet_reminders",
                                "marketing_emails", "push_notifications"]
                
                for setting in valid_settings:
                    if setting in notification_data:
                        current_value = getattr(notification_settings, setting)
                        new_value = bool(notification_data[setting])
                        
                        if current_value != new_value:
                            setattr(notification_settings, setting, new_value)
                            changes.append(
                                f"{setting.replace('_', ' ')} changed from "
                                f"{'enabled' if current_value else 'disabled'} to "
                                f"{'enabled' if new_value else 'disabled'}"
                            )
                
                if changes:
                    notification_settings.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Only send notification if account updates are enabled (unless we're enabling them)
        send_notification = True
        if notification_settings and "account_updates" not in notification_data:
            send_notification = notification_settings.account_updates
        
        if changes and send_notification:
            create_notification(
                db,
                user_id,
                "Notification Preferences Updated",
                "Your notification settings were modified: " + ", ".join(changes),
                "account"
            )
        
        return {
            "message": "Notification settings updated successfully",
            "changes": changes,
            "current_settings": {
                "new_messages": notification_settings.new_messages,
                "account_updates": notification_settings.account_updates,
                "pet_reminders": notification_settings.pet_reminders,
                "marketing_emails": notification_settings.marketing_emails,
                "push_notifications": notification_settings.push_notifications
            } if notification_settings else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error updating notification preferences: {str(e)}"
        )

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# In-memory token storage (replace with Redis in production)
reset_tokens = {}


@router.get("/{user_id}/privacy-settings")
async def get_user_privacy_settings(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "email": user.email,
            "has_password": bool(user.hashed_password),
            "is_verified": user.is_verified
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
async def change_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not pwd_context.verify(password_data.get("current_password"), user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        user.hashed_password = pwd_context.hash(password_data.get("new_password"))
        db.commit()
        
        # Create security notification
        create_notification(
            db,
            user_id,
            "Password Changed",
            "Your password was successfully updated",
            "security"
        )
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# @router.post("/{user_id}/request-password-reset")
# async def request_user_password_reset(
#     user_id: int,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     try:
#         user = db.query(models.User).filter(models.User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         reset_token = secrets.token_urlsafe(32)
#         reset_tokens[reset_token] = {
#             "user_id": user_id,
#             "expires_at": datetime.utcnow() + timedelta(hours=1)
#         }
        
#         # Send email in background
#         background_tasks.add_task(
#             send_password_reset_email,
#             email=user.email,
#             reset_token=reset_token
#         )
        
#         return {"message": "Password reset email sent"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/reset-password")
# async def reset_password(
#     token: str = Query(...),
#     new_password: str = Query(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify token exists and isn't expired
#         token_data = reset_tokens.get(token)
#         if not token_data or token_data["expires_at"] < datetime.utcnow():
#             raise HTTPException(status_code=400, detail="Invalid or expired token")
        
#         # Get user from token data
#         user = db.query(models.User).filter(models.User.id == token_data["user_id"]).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Update password
#         user.hashed_password = pwd_context.hash(new_password)
#         db.commit()
        
#         # Clean up used token
#         del reset_tokens[token]
        
#         return {"message": "Password reset successfully"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))


# # Password Reset Endpoints
# @router.post("/{user_id}/request-password-reset")
# async def request_user_password_reset(
#     user_id: int,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     # Find user
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Generate and save hashed token + expiry
#     raw_token = secrets.token_urlsafe(32)  # Raw token for email
#     user.reset_token = pwd_context.hash(raw_token)  # Store hashed
#     user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
#     db.commit()

#     # Send email (background)
#     background_tasks.add_task(
#         send_password_reset_email,
#         email=user.email,
#         reset_token=raw_token  # Send raw token
#     )

#     return {"message": "Password reset email sent"}


def check_rate_limit(request: Request, limit: int = 5, window: int = 3600):
    """Basic rate limiting using client IP."""
    client_ip = request.client.host
    now = datetime.utcnow().timestamp()
    
    # Clear old entries
    _request_counts[client_ip] = [
        t for t in _request_counts.get(client_ip, []) 
        if now - t < window
    ]
    
    # Check limit
    if len(_request_counts.get(client_ip, [])) >= limit:
        raise HTTPException(
            status_code=429, 
            detail="Too many requests. Try again later."
        )
    
    # Record new request
    _request_counts.setdefault(client_ip, []).append(now)

@router.post("/request-password-reset")
async def request_password_reset(
    request: Request,
    email: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Endpoint to request password reset with simple rate limiting."""
    # Basic rate limiting (5 requests/hour per IP)
    check_rate_limit(request)
    
    # Rest of your existing code...
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # try:
    #     raw_token = secrets.token_urlsafe(32)
    #     user.reset_token = pwd_context.hash(raw_token)
    #     user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    #     db.commit()

    #     if background_tasks:
    #         background_tasks.add_task(
    #             send_password_reset_email,
    #             email=user.email,
    #             reset_token=raw_token
    #         )
    #     else:
    #         await send_password_reset_email(user.email, raw_token)

    #     return {"message": "Password reset email sent"}

    # except Exception as e:
    #     db.rollback()
    #     raise HTTPException(status_code=500, detail=str(e))

    try:
        # Transaction 1 - Database update
        raw_token = secrets.token_urlsafe(32)
        user.reset_token = pwd_context.hash(raw_token)
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()  # Final commit here
    
        # Transaction 2 - Email (can fail without affecting DB)
        try:
            if background_tasks:
                background_tasks.add_task(...)
            else:
                await send_password_reset_email(...)
        except Exception as email_error:
            print(f"Email failed but DB was updated: {email_error}")
    
        return {"message": "Password reset email sent"}
    except Exception as db_error:
        db.rollback()
        raise HTTPException(...)


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),  # From frontend form
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Find user with valid token
    user = db.query(User).filter(
        User.reset_token.isnot(None),
        User.reset_token_expires_at > datetime.utcnow()
    ).first()

    # Verify token
    if not user or not pwd_context.verify(token, user.reset_token):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Update password and clear token
    user.hashed_password = pwd_context.hash(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()

    return {"message": "Password reset successfully"}




