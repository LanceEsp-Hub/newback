from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.models import User
from ..models.models import UserReport, BlockedUser
from ..database.database import get_db
from sqlalchemy import and_, or_
from typing import Optional

router = APIRouter(prefix="/api/security", tags=["security"])

@router.post("/report-user")
async def report_user(
    reported_user_id: int = Body(...),
    reporter_id: int = Body(...),
    reason: str = Body(...),
    description: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Report a suspicious or problematic user"""
    try:
        # Validate reason
        valid_reasons = ["harassment", "spam", "inappropriate_content", "fake_profile", "other"]
        if reason not in valid_reasons:
            raise HTTPException(status_code=400, detail="Invalid report reason")
        
        # Check if users exist
        reporter = db.query(User).filter(User.id == reporter_id).first()
        reported_user = db.query(User).filter(User.id == reported_user_id).first()
        
        if not reporter or not reported_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if reporter_id == reported_user_id:
            raise HTTPException(status_code=400, detail="Cannot report yourself")
        
        # Check if already reported by this user
        existing_report = db.query(UserReport).filter(
            and_(
                UserReport.reporter_id == reporter_id,
                UserReport.reported_user_id == reported_user_id,
                UserReport.status == "pending"
            )
        ).first()
        
        if existing_report:
            raise HTTPException(status_code=400, detail="You have already reported this user")
        
        # Create new report
        new_report = UserReport(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reason=reason,
            description=description,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(new_report)
        db.commit()
        
        return {
            "success": True,
            "message": "User reported successfully. Our team will review this report.",
            "report_id": new_report.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/block-user")
async def block_user(
    blocker_id: int = Body(...),
    blocked_user_id: int = Body(...),
    db: Session = Depends(get_db)
):
    """Block a user to prevent them from messaging you"""
    try:
        # Check if users exist
        blocker = db.query(User).filter(User.id == blocker_id).first()
        blocked_user = db.query(User).filter(User.id == blocked_user_id).first()
        
        if not blocker or not blocked_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if blocker_id == blocked_user_id:
            raise HTTPException(status_code=400, detail="Cannot block yourself")
        
        # Check if already blocked
        existing_block = db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_user_id == blocked_user_id
            )
        ).first()
        
        if existing_block:
            raise HTTPException(status_code=400, detail="User is already blocked")
        
        # Create new block
        new_block = BlockedUser(
            blocker_id=blocker_id,
            blocked_user_id=blocked_user_id,
            created_at=datetime.utcnow()
        )
        
        db.add(new_block)
        db.commit()
        
        return {
            "success": True,
            "message": "User blocked successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unblock-user")
async def unblock_user(
    blocker_id: int = Body(...),
    blocked_user_id: int = Body(...),
    db: Session = Depends(get_db)
):
    """Unblock a previously blocked user"""
    try:
        # Find and remove the block
        block = db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_user_id == blocked_user_id
            )
        ).first()
        
        if not block:
            raise HTTPException(status_code=404, detail="User is not blocked")
        
        db.delete(block)
        db.commit()
        
        return {
            "success": True,
            "message": "User unblocked successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blocked-users/{user_id}")
async def get_blocked_users(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get list of users blocked by the current user"""
    try:
        blocked_users = db.query(BlockedUser).filter(
            BlockedUser.blocker_id == user_id
        ).all()
        
        result = []
        for block in blocked_users:
            blocked_user = db.query(User).filter(User.id == block.blocked_user_id).first()
            if blocked_user:
                result.append({
                    "id": blocked_user.id,
                    "name": blocked_user.name,
                    "blocked_at": block.created_at.isoformat()
                })
        
        return {"blocked_users": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-block-status")
async def check_block_status(
    user1_id: int,
    user2_id: int,
    db: Session = Depends(get_db)
):
    """Check if either user has blocked the other"""
    try:
        # Check if user1 blocked user2 or vice versa
        block_exists = db.query(BlockedUser).filter(
            or_(
                and_(BlockedUser.blocker_id == user1_id, BlockedUser.blocked_user_id == user2_id),
                and_(BlockedUser.blocker_id == user2_id, BlockedUser.blocked_user_id == user1_id)
            )
        ).first()
        
        return {
            "is_blocked": block_exists is not None,
            "blocker_id": block_exists.blocker_id if block_exists else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
