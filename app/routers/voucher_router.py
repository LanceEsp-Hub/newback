from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from app.database.database import get_db
from app.models.models import Voucher, VoucherUsage, User, UserVoucher
from app.schemas.ecommerce_schemas import (
    VoucherCreate, VoucherResponse, VoucherUsageCreate, 
    VoucherUsageResponse, VoucherValidationRequest, VoucherValidationResponse,
    UserVoucherCreate, UserVoucherResponse
)
# from app.auth.dependencies import admin_required  # Temporarily disabled for testing

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Get all users for admin assignment (Admin only)"""
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        result = []
        for user in users:
            # Add null checks for all fields
            user_data = {
                "id": getattr(user, 'id', None),
                "name": getattr(user, 'name', 'Unknown') or 'Unknown',
                "email": getattr(user, 'email', 'No email') or 'No email',
                "is_active": getattr(user, 'is_active', True)
            }
            result.append(user_data)
        
        return result
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return []

@router.get("/test-users")
def test_users(db: Session = Depends(get_db)):
    """Test endpoint to debug user model"""
    try:
        users = db.query(User).limit(5).all()
        return {
            "total_users": len(users),
            "sample_user": {
                "id": users[0].id if users else None,
                "name": users[0].name if users else None,
                "email": users[0].email if users else None,
                "is_active": users[0].is_active if users else None
            } if users else None
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/", response_model=VoucherResponse)
def create_voucher(
    voucher: VoucherCreate,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Create a new voucher (Admin only)"""
    # Check if voucher code already exists
    existing_voucher = db.query(Voucher).filter(Voucher.code == voucher.code).first()
    if existing_voucher:
        raise HTTPException(status_code=400, detail="Voucher code already exists")
    
    # Validate discount type
    if voucher.discount_type not in ['percentage', 'fixed']:
        raise HTTPException(status_code=400, detail="Invalid discount type")
    
    # Validate dates
    if voucher.start_date >= voucher.end_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Create voucher
    db_voucher = Voucher(
        **voucher.dict(),
        created_by=1  # Default admin user ID for testing
    )
    db.add(db_voucher)
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

@router.get("/", response_model=List[VoucherResponse])
def get_all_vouchers(
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Get all vouchers (Admin only)"""
    vouchers = db.query(Voucher).order_by(Voucher.created_at.desc()).all()
    return vouchers

@router.get("/{voucher_id}", response_model=VoucherResponse)
def get_voucher(
    voucher_id: int,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Get a specific voucher (Admin only)"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return voucher

@router.put("/{voucher_id}", response_model=VoucherResponse)
def update_voucher(
    voucher_id: int,
    voucher: VoucherCreate,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Update a voucher (Admin only)"""
    db_voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not db_voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    # Check if code is being changed and if it already exists
    if voucher.code != db_voucher.code:
        existing_voucher = db.query(Voucher).filter(Voucher.code == voucher.code).first()
        if existing_voucher:
            raise HTTPException(status_code=400, detail="Voucher code already exists")
    
    # Update voucher
    for key, value in voucher.dict().items():
        setattr(db_voucher, key, value)
    
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

@router.delete("/{voucher_id}")
def delete_voucher(
    voucher_id: int,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Delete a voucher (Admin only)"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    # Check if voucher has any usage records
    usage_count = db.query(VoucherUsage).filter(VoucherUsage.voucher_id == voucher_id).count()
    if usage_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete voucher. It has been used {usage_count} time(s). Consider deactivating instead."
        )
    
    # Check if voucher has any user assignments
    assignment_count = db.query(UserVoucher).filter(UserVoucher.voucher_id == voucher_id).count()
    if assignment_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete voucher. It has been assigned to {assignment_count} user(s). Consider deactivating instead."
        )
    
    db.delete(voucher)
    db.commit()
    return {"message": "Voucher deleted successfully"}

@router.put("/{voucher_id}/deactivate")
def deactivate_voucher(
    voucher_id: int,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Deactivate a voucher (Admin only)"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    voucher.is_active = False
    db.commit()
    return {"message": "Voucher deactivated successfully"}

@router.post("/validate", response_model=VoucherValidationResponse)
def validate_voucher(
    request: VoucherValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a voucher code for a user"""
    # Find the voucher
    voucher = db.query(Voucher).filter(
        Voucher.code == request.code,
        Voucher.is_active == True
    ).first()
    
    if not voucher:
        return VoucherValidationResponse(
            is_valid=False,
            message="Invalid voucher code"
        )
    
    # Check if voucher is within date range
    now = datetime.utcnow()
    if now < voucher.start_date or now > voucher.end_date:
        return VoucherValidationResponse(
            is_valid=False,
            message="Voucher is not active"
        )
    
    # Check usage limit
    if voucher.usage_limit and voucher.used_count >= voucher.usage_limit:
        return VoucherValidationResponse(
            is_valid=False,
            message="Voucher usage limit reached"
        )
    
    # Check minimum order amount
    if request.subtotal < float(voucher.min_order_amount):
        return VoucherValidationResponse(
            is_valid=False,
            message=f"Minimum order amount of ${float(voucher.min_order_amount)} required"
        )
    
    # Calculate discount
    discount_amount = 0
    shipping_discount = 0
    
    if voucher.discount_type == 'percentage':
        discount_amount = request.subtotal * (float(voucher.discount_value) / 100)
        if voucher.max_discount:
            discount_amount = min(discount_amount, float(voucher.max_discount))
    else:  # fixed amount
        discount_amount = float(voucher.discount_value)
    
    # Apply shipping discount if free shipping
    if voucher.free_shipping:
        shipping_discount = request.delivery_fee
    
    return VoucherValidationResponse(
        is_valid=True,
        voucher=voucher,
        discount_amount=discount_amount,
        shipping_discount=shipping_discount,
        message="Voucher applied successfully"
    )

@router.post("/apply", response_model=VoucherUsageResponse)
def apply_voucher(
    usage: VoucherUsageCreate,
    db: Session = Depends(get_db)
):
    """Apply a voucher to an order"""
    # Validate voucher exists and is active
    voucher = db.query(Voucher).filter(
        Voucher.id == usage.voucher_id,
        Voucher.is_active == True
    ).first()
    
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    # Check if voucher is within date range
    now = datetime.utcnow()
    if now < voucher.start_date or now > voucher.end_date:
        raise HTTPException(status_code=400, detail="Voucher is not active")
    
    # Check usage limit
    if voucher.usage_limit and voucher.used_count >= voucher.usage_limit:
        raise HTTPException(status_code=400, detail="Voucher usage limit reached")
    
    # Create voucher usage record
    db_usage = VoucherUsage(**usage.dict())
    db.add(db_usage)
    
    # Update voucher usage count
    voucher.used_count += 1
    
    db.commit()
    db.refresh(db_usage)
    return db_usage

@router.get("/usage/{voucher_id}", response_model=List[VoucherUsageResponse])
def get_voucher_usage(
    voucher_id: int,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Get usage history for a voucher (Admin only)"""
    usages = db.query(VoucherUsage).filter(VoucherUsage.voucher_id == voucher_id).all()
    return usages

@router.post("/assign", response_model=UserVoucherResponse)
def assign_voucher_to_user(
    assignment: UserVoucherCreate,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Assign a voucher to a specific user (Admin only)"""
    # Check if user exists
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if voucher exists and is active
    voucher = db.query(Voucher).filter(Voucher.id == assignment.voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if not voucher.is_active:
        raise HTTPException(status_code=400, detail="Voucher is not active")
    
    # Check if voucher is already assigned to this user
    existing_assignment = db.query(UserVoucher).filter(
        UserVoucher.user_id == assignment.user_id,
        UserVoucher.voucher_id == assignment.voucher_id,
        UserVoucher.is_active == True
    ).first()
    
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Voucher is already assigned to this user")
    
    # Create user voucher assignment
    user_voucher = UserVoucher(
        user_id=assignment.user_id,
        voucher_id=assignment.voucher_id,
        assigned_by=assignment.assigned_by or 1  # Default admin ID for testing
    )
    
    db.add(user_voucher)
    db.commit()
    db.refresh(user_voucher)
    
    # Return with voucher details
    return {
        "id": user_voucher.id,
        "user_id": user_voucher.user_id,
        "voucher_id": user_voucher.voucher_id,
        "assigned_at": user_voucher.assigned_at,
        "assigned_by": user_voucher.assigned_by,
        "is_active": user_voucher.is_active,
        "voucher": voucher
    }

@router.get("/user/{user_id}", response_model=List[UserVoucherResponse])
def get_user_vouchers(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all vouchers assigned to a specific user"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user voucher assignments with voucher details
    user_vouchers = db.query(UserVoucher).filter(
        UserVoucher.user_id == user_id,
        UserVoucher.is_active == True
    ).all()
    
    result = []
    for user_voucher in user_vouchers:
        voucher = db.query(Voucher).filter(Voucher.id == user_voucher.voucher_id).first()
        if voucher and voucher.is_active:
            result.append({
                "id": user_voucher.id,
                "user_id": user_voucher.user_id,
                "voucher_id": user_voucher.voucher_id,
                "assigned_at": user_voucher.assigned_at,
                "assigned_by": user_voucher.assigned_by,
                "is_active": user_voucher.is_active,
                "voucher": voucher
            })
    
    return result

@router.delete("/user/{user_id}/voucher/{voucher_id}")
def remove_user_voucher(
    user_id: int,
    voucher_id: int,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Remove a voucher assignment from a user (Admin only)"""
    user_voucher = db.query(UserVoucher).filter(
        UserVoucher.user_id == user_id,
        UserVoucher.voucher_id == voucher_id,
        UserVoucher.is_active == True
    ).first()
    
    if not user_voucher:
        raise HTTPException(status_code=404, detail="Voucher assignment not found")
    
    user_voucher.is_active = False
    db.commit()
    
    return {"message": "Voucher assignment removed successfully"} 
