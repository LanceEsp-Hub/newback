# backend\app\routers\message_router.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.models import Message, Conversation, User, BlockedUser
from ..database.database import get_db
from fastapi import UploadFile, File
from pathlib import Path
import os
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import joinedload  # Add this import
from supabase import create_client
import uuid

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_MESSAGE_BUCKET", "messages")

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase initialized successfully for messages")
except Exception as e:
    print(f"Supabase init failed for messages: {str(e)}")
    raise RuntimeError("Supabase initialization failed for messages") from e

def check_users_blocked(user1_id: int, user2_id: int, db: Session) -> bool:
    """Check if either user has blocked the other"""
    block_exists = db.query(BlockedUser).filter(
        or_(
            and_(BlockedUser.blocker_id == user1_id, BlockedUser.blocked_user_id == user2_id),
            and_(BlockedUser.blocker_id == user2_id, BlockedUser.blocked_user_id == user1_id)
        )
    ).first()
    return block_exists is not None

# @router.post("/start-conversation")
# async def start_conversation(
#     user1_id: int = Body(...),
#     user2_id: int = Body(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Check if conversation already exists
#         existing_conversation = db.query(Conversation).filter(
#             or_(
#                 and_(Conversation.user1 == user1_id, Conversation.user2 == user2_id),
#                 and_(Conversation.user1 == user2_id, Conversation.user2 == user1_id)
#             )
#         ).first()
        
#         if existing_conversation:
#             return {"conversation_id": existing_conversation.id}
        
#         # Create new conversation
#         new_conversation = Conversation(
#             user1=user1_id,
#             user2=user2_id
#         )
        
#         db.add(new_conversation)
#         db.commit()
        
#         return {"conversation_id": new_conversation.id}
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-conversation")
async def start_conversation(
    user1_id: int = Body(...),
    user2_id: int = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Check if users are blocked
        if check_users_blocked(user1_id, user2_id, db):
            raise HTTPException(status_code=403, detail="Cannot start conversation with blocked user")
        
        # Check if conversation already exists
        existing_conversation = db.query(Conversation).filter(
            or_(
                and_(Conversation.user1 == user1_id, Conversation.user2 == user2_id),
                and_(Conversation.user1 == user2_id, Conversation.user2 == user1_id)
            )
        ).first()
        
        if existing_conversation:
            return {"conversation_id": existing_conversation.id}
        
        # Create new conversation
        new_conversation = Conversation(
            user1=user1_id,
            user2=user2_id
        )
        
        db.add(new_conversation)
        db.commit()
        
        return {"conversation_id": new_conversation.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/send")
# async def send_message(
#     conversation_id: int = Body(...),
#     sender_id: int = Body(...),
#     text: str = Body(None),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify conversation exists and sender is part of it
#         conversation = db.query(Conversation).filter(
#             Conversation.id == conversation_id,
#             or_(Conversation.user1 == sender_id, Conversation.user2 == sender_id)
#         ).first()
        
#         if not conversation:
#             raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
        
#         # Determine receiver_id
#         receiver_id = conversation.user2 if conversation.user1 == sender_id else conversation.user1
        
#         if not text:
#             raise HTTPException(status_code=400, detail="Message text cannot be empty")
        
#         new_message = Message(
#             sender_id=sender_id,
#             receiver_id=receiver_id,
#             conversation_id=conversation_id,
#             text=text,
#             timestamp=datetime.now(),
#             is_read=False,
#             image_url=None
#         )
        
#         db.add(new_message)
#         db.commit()
        
#         return {"success": True, "message_id": new_message.id}
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_message(
    conversation_id: int = Body(...),
    sender_id: int = Body(...),
    text: str = Body(None),
    db: Session = Depends(get_db)
):
    try:
        # Verify conversation exists and sender is part of it
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            or_(Conversation.user1 == sender_id, Conversation.user2 == sender_id)
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
        
        # Determine receiver_id
        receiver_id = conversation.user2 if conversation.user1 == sender_id else conversation.user1
        
        # Check if users are blocked
        if check_users_blocked(sender_id, receiver_id, db):
            raise HTTPException(status_code=403, detail="Cannot send message to blocked user")
        
        if not text:
            raise HTTPException(status_code=400, detail="Message text cannot be empty")
        
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            conversation_id=conversation_id,
            text=text,
            timestamp=datetime.now(),
            is_read=False,
            image_url=None
        )
        
        db.add(new_message)
        db.commit()
        
        return {"success": True, "message_id": new_message.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/conversation/{conversation_id}")
async def get_conversation_messages(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Verify user is part of the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            or_(Conversation.user1 == user_id, Conversation.user2 == user_id)
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
        
        # Get all messages in the conversation
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.asc()).all()
        
        # Mark messages as read
        db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.receiver_id == user_id,
            Message.is_read == False
        ).update({"is_read": True})
        db.commit()
        
        return {
            "conversation_id": conversation_id,
            "other_user_id": conversation.user2 if conversation.user1 == user_id else conversation.user1,
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_read": msg.is_read,
                    "image_url": msg.image_url  # Now stored as full Supabase URL
                } for msg in messages
            ]
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
async def upload_message_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read file content
        content = await file.read()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(file.filename).suffix
        filename = f"{timestamp}_{unique_id}{file_extension}"
        
        # Upload to Supabase Storage
        try:
            result = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=filename,
                file=content,
                file_options={"content-type": file.content_type}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
            
            return {
                "success": True,
                "filename": filename
            }
            
        except Exception as supabase_error:
            print(f"Supabase upload error: {str(supabase_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(supabase_error)}")

    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-with-image")
async def send_message_with_image(
    conversation_id: int = Body(...),
    sender_id: int = Body(...),
    text: str = Body(None),
    image_url: str = Body(None),
    db: Session = Depends(get_db)
):
    try:
        # Verify conversation exists and sender is part of it
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            or_(Conversation.user1 == sender_id, Conversation.user2 == sender_id)
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
        
        # Determine receiver_id
        receiver_id = conversation.user2 if conversation.user1 == sender_id else conversation.user1
        
        if not text and not image_url:
            raise HTTPException(status_code=400, detail="Message must have text or image")

        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            conversation_id=conversation_id,
            text=text,
            image_url=image_url,
            timestamp=datetime.now(),
            is_read=False
        )
        
        db.add(new_message)
        db.commit()
        
        return {"success": True, "message_id": new_message.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/conversations")
async def get_user_conversations(
    current_user_id: int,
    other_user_id: int = None,  # New optional parameter
    db: Session = Depends(get_db)
):
    """Get conversations for the current user, optionally filtered by another user"""
    try:
        # Base query
        query = db.query(Conversation).filter(
            or_(
                Conversation.user1 == current_user_id,
                Conversation.user2 == current_user_id
            )
        ).options(
            joinedload(Conversation.user1_ref),
            joinedload(Conversation.user2_ref)
        )

        # If specific user ID provided, filter for that conversation
        if other_user_id is not None:
            query = query.filter(
                or_(
                    Conversation.user2 == other_user_id,
                    Conversation.user1 == other_user_id
                )
            )

        conversations = query.all()

        result = []
        for conv in conversations:
            other_user = (conv.user2_ref if conv.user1 == current_user_id 
                         else conv.user1_ref)
            
            result.append({
                "conversation_id": conv.id,
                "other_user": {
                    "id": other_user.id,
                    "name": other_user.name,
                    "profile_picture": other_user.profile_picture
                }
            })
        
        return {"conversations": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




















































# @router.get("/conversations")
# async def get_user_conversations(
#     current_user_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get all conversations for the current user with last message and unread counts"""
#     try:
#         # Get all conversations for the user
#         conversations = db.query(Conversation).filter(
#             or_(
#                 Conversation.user1 == current_user_id,
#                 Conversation.user2 == current_user_id
#             )
#         ).options(
#             joinedload(Conversation.user1_ref),
#             joinedload(Conversation.user2_ref),
#             joinedload(Conversation.messages)
#         ).all()

#         result = []
#         for conv in conversations:
#             # Determine the other user
#             other_user = (conv.user2_ref if conv.user1 == current_user_id 
#                          else conv.user1_ref)
            
#             # Get last message
#             last_message = max(conv.messages, key=lambda m: m.timestamp) if conv.messages else None
            
#             # Count unread messages
#             unread_count = sum(
#                 1 for msg in conv.messages 
#                 if msg.receiver_id == current_user_id and not msg.is_read
#             )
            
#             result.append({
#                 "conversation_id": conv.id,
#                 "other_user": {
#                     "id": other_user.id,
#                     "name": other_user.name,
#                     "profile_picture": other_user.profile_picture
#                 },
#                 "last_message": {
#                     "text": last_message.text if last_message else None,
#                     "timestamp": last_message.timestamp.isoformat() if last_message else None,
#                     "is_read": last_message.is_read if last_message else None
#                 },
#                 "unread_count": unread_count
#             })
        
#         # Sort by last message timestamp (newest first)
#         result.sort(
#             key=lambda x: x["last_message"]["timestamp"] or "1970-01-01",
#             reverse=True
#         )
        
#         return {"conversations": result}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/conversations/{user_id}")
# async def get_user_conversations(
#     user_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Get all conversations for the user
#         conversations = db.query(Conversation).filter(
#             or_(Conversation.user1 == user_id, Conversation.user2 == user_id)
#         ).all()
        
#         result = []
#         for conv in conversations:
#             # Get the other user in the conversation
#             other_user_id = conv.user2 if conv.user1 == user_id else conv.user1
#             other_user = db.query(User).filter(User.id == other_user_id).first()
            
#             if not other_user:
#                 continue
            
#             # Get last message in the conversation
#             last_message = db.query(Message).filter(
#                 Message.conversation_id == conv.id
#             ).order_by(Message.timestamp.desc()).first()
            
#             result.append({
#                 "conversation_id": conv.id,
#                 "other_user": {
#                     "id": other_user.id,
#                     "name": other_user.name,
#                     "profile_picture": other_user.profile_picture
#                 },
#                 "last_message": {
#                     "text": last_message.text if last_message else None,
#                     "timestamp": last_message.timestamp.isoformat() if last_message else None,
#                     "is_read": last_message.is_read if last_message else None,
#                     "has_image": last_message.image_url is not None if last_message else False
#                 },
#                 "unread_count": db.query(func.count(Message.id)).filter(
#                     Message.conversation_id == conv.id,
#                     Message.receiver_id == user_id,
#                     Message.is_read == False
#                 ).scalar()
#             })
        
#         # Sort conversations by last message timestamp
#         result.sort(
#             key=lambda x: x["last_message"]["timestamp"] or "",
#             reverse=True
#         )
        
#         return {"conversations": result}
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# @router.get("/conversations")
# async def get_user_conversations(
#     current_user_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get all conversations for the current user"""
#     try:
#         conversations = db.query(Conversation).filter(
#             or_(
#                 Conversation.user1 == current_user_id,
#                 Conversation.user2 == current_user_id
#             )
#         ).options(
#             joinedload(Conversation.user1_ref),
#             joinedload(Conversation.user2_ref)
#         ).all()

#         result = []
#         for conv in conversations:
#             other_user = (conv.user2_ref if conv.user1 == current_user_id 
#                          else conv.user1_ref)
            
#             result.append({
#                 "conversation_id": conv.id,
#                 "other_user": {
#                     "id": other_user.id,
#                     "name": other_user.name,
#                     "profile_picture": other_user.profile_picture
#                 }
#             })
        
#         return {"conversations": result}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
