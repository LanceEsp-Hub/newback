# backend/app/routers/notification_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import UserNotification, User, Notification
from datetime import datetime, timedelta
from app.models import models
from sqlalchemy import func, and_, or_


router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/unread-count/{user_id}")
async def get_unread_notification_count(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get count of unread notifications for the user (for Navbar badge)
    """
    try:
        count = db.query(UserNotification).filter(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False
        ).count()
        
        return {"unread_count": count}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching notification count: {str(e)}"
        )

# @router.get("/user/{user_id}")
# async def get_user_notifications(
#     user_id: int,
#     limit: int = 5,  # Default to 5 recent notifications for Navbar
#     db: Session = Depends(get_db)
# ):
#     """
#     Get recent notifications for the user (for Navbar dropdown)
#     """
#     try:
#         # Verify user exists
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         notifications = db.query(UserNotification).filter(
#             UserNotification.user_id == user_id
#         ).order_by(
#             UserNotification.created_at.desc()
#         ).limit(limit).all()

#         return {
#             "notifications": [
#                 {
#                     "id": n.id,
#                     "title": n.title,
#                     "message": n.message,
#                     "is_read": n.is_read,
#                     "created_at": n.created_at.isoformat(),
#                     "type": n.notification_type
#                 }
#                 for n in notifications
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching notifications: {str(e)}"
#         )

# @router.get("/user/{user_id}")
# async def get_user_notifications(
#     user_id: int,
#     limit: int = 5,  # Default to 5 recent notifications for Navbar
#     db: Session = Depends(get_db)
# ):
#     """
#     Get recent notifications for the user (for Navbar dropdown)
#     Only returns notifications of types that are enabled in user's preferences
#     """
#     try:
#         # Verify user exists and get their notification preferences
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Get the user's notification preferences
#         notification_prefs = None
#         if user.notification_id:
#             notification_prefs = db.query(UserNotification).filter(
#                 UserNotification.id == user.notification_id
#             ).first()

#         # Base query for notifications
#         query = db.query(UserNotification).filter(
#             UserNotification.user_id == user_id
#         )

#         # Filter by enabled notification types if preferences exist
#         if notification_prefs:
#             # Build filter conditions based on enabled preferences
#             conditions = []
            
#             # Map notification types to preference flags
#             type_mapping = {
#                 "message": notification_prefs.new_messages,
#                 "account": notification_prefs.account_updates,
#                 "pet": notification_prefs.pet_reminders,
#                 "marketing": notification_prefs.marketing_emails,
#                 "system": notification_prefs.push_notifications
#             }

#             # Add condition for each enabled notification type
#             for notif_type, is_enabled in type_mapping.items():
#                 if is_enabled:
#                     conditions.append(
#                         UserNotification.notification_type == notif_type
#                     )

#             # Apply the filters if any conditions exist
#             if conditions:
#                 query = query.filter(or_(*conditions))

#         # Execute the query with sorting and limit
#         notifications = query.order_by(
#             UserNotification.created_at.desc()
#         ).limit(limit).all()

#         return {
#             "notifications": [
#                 {
#                     "id": n.id,
#                     "title": n.title,
#                     "message": n.message,
#                     "is_read": n.is_read,
#                     "created_at": n.created_at.isoformat(),
#                     "type": n.notification_type
#                 }
#                 for n in notifications
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching notifications: {str(e)}"
#         )

# @router.get("/user/{user_id}")
# async def get_user_notifications(
#     user_id: int,
#     limit: int = 5,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Basic query without preference filtering first
#         notifications = db.query(UserNotification).filter(
#             UserNotification.user_id == user_id
#         ).order_by(
#             UserNotification.created_at.desc()
#         ).limit(limit).all()

#         return {
#             "notifications": [
#                 {
#                     "id": n.id,
#                     "title": n.title,
#                     "message": n.message,
#                     "is_read": n.is_read,
#                     "created_at": n.created_at.isoformat(),
#                     "type": n.notification_type
#                 }
#                 for n in notifications
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching notifications: {str(e)}"
#         )

@router.get("/user/{user_id}")
async def get_user_notifications(
    user_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get preferences through the relationship
        notification_prefs = user.notification_settings
        
        if not notification_prefs:
            return {"notifications": []}

        conditions = []
        if notification_prefs.account_updates:
            conditions.append(UserNotification.notification_type == "account")
        if notification_prefs.pet_reminders:
            conditions.append(UserNotification.notification_type == "pet")
        if notification_prefs.marketing_emails:
            conditions.append(UserNotification.notification_type == "marketing")
        if notification_prefs.push_notifications:
            conditions.append(UserNotification.notification_type == "system")


        if not conditions:
            return {"notifications": []}

        notifications = db.query(UserNotification).filter(
            UserNotification.user_id == user_id,
            or_(*conditions)
        ).order_by(
            UserNotification.created_at.desc()
        ).limit(limit).all()

        return {
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                    "type": n.notification_type
                }
                for n in notifications
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching notifications: {str(e)}"
        )
    
# backend/app/routers/notification_router.py
@router.get("/check-settings/{user_id}")
async def check_notification_settings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if user has configured notification settings
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if notification settings exist
        settings = db.query(UserNotification).filter(
            UserNotification.id == user.notification_id
        ).first()

        return {"has_settings": settings is not None}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking notification settings: {str(e)}"
        )

# Add this to your notification_router.py
@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    try:
        notification = db.query(models.UserNotification).filter(
            models.UserNotification.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
        notification.is_read = True
        db.commit()
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Find the notification
        notification = db.query(models.UserNotification).filter(
            models.UserNotification.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
        # Update the read status
        notification.is_read = True
        db.commit()
        
        return {
            "success": True,
            "message": "Notification marked as read",
            "notification_id": notification_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
# backend/app/routers/notification_router.py
@router.patch("/mark-all-read/{user_id}")
async def mark_all_notifications_read(
    user_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Update all unread notifications for this user
        result = db.query(UserNotification).filter(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False
        ).update({"is_read": True})
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Marked {result} notifications as read"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )