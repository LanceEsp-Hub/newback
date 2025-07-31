

from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, Form, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, cast, Integer
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import uuid
import os
from fastapi.responses import FileResponse, JSONResponse

from app.database.database import get_db
from app.models import models

UPLOAD_DIR = Path("app/uploads/success_stories")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/admin", tags=["admin"])



def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total_size = 0
    try:
        # Convert relative path to absolute path
        if not os.path.isabs(path):
            # Get the current working directory and join with the path
            current_dir = os.getcwd()
            abs_path = os.path.join(current_dir, path)
        else:
            abs_path = path
            
        print(f"Checking directory: {abs_path}")  # Debug log
        
        if os.path.exists(abs_path):
            if os.path.isdir(abs_path):
                for dirpath, dirnames, filenames in os.walk(abs_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            if os.path.exists(filepath) and os.path.isfile(filepath):
                                file_size = os.path.getsize(filepath)
                                total_size += file_size
                                print(f"File: {filepath}, Size: {file_size} bytes")  # Debug log
                        except (OSError, IOError) as e:
                            print(f"Error accessing file {filepath}: {e}")
                            continue
            else:
                # If it's a file, get its size
                total_size = os.path.getsize(abs_path)
        else:
            print(f"Directory does not exist: {abs_path}")
            # Create directory if it doesn't exist
            try:
                os.makedirs(abs_path, exist_ok=True)
                print(f"Created directory: {abs_path}")
            except Exception as e:
                print(f"Could not create directory {abs_path}: {e}")
                
    except Exception as e:
        print(f"Error calculating directory size for {path}: {e}")
    
    print(f"Total size for {path}: {total_size} bytes")  # Debug log
    return total_size

def format_bytes(bytes_size):
    """Convert bytes to human readable format"""
    if bytes_size == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

@router.get("/test")
async def test_admin_router():
    """Test endpoint to verify admin router is working"""
    return {"message": "Admin router is working!", "timestamp": datetime.utcnow()}



@router.get("/test")
async def test_admin_router():
    """Test endpoint to verify admin router is working"""
    return {"message": "Admin router is working!", "timestamp": datetime.utcnow()}


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    time_range: str = Query("all", description="Time range: day, week, month, year, all"),
    db: Session = Depends(get_db)
):
    time_filters = {
        "day": datetime.utcnow() - timedelta(days=1),
        "week": datetime.utcnow() - timedelta(weeks=1),
        "month": datetime.utcnow() - timedelta(days=30),
        "year": datetime.utcnow() - timedelta(days=365),
        "all": None
    }
    time_filter = time_filters.get(time_range.lower())

    def apply_time_filter(query, column):
        if time_filter:
            return query.filter(column >= time_filter)
        return query

    # User Statistics
    users_query = apply_time_filter(db.query(models.User), models.User.created_at)
    total_users = users_query.count()
    active_users = users_query.filter(models.User.is_active == True).count()
    verified_users = users_query.filter(models.User.is_verified == True).count()

    # Pet Statistics
    pets_query = apply_time_filter(db.query(models.Pet), models.Pet.created_at)
    total_pets = pets_query.count()
    published_pets = pets_query.filter(models.Pet.is_published == True).count()
    approved_pets = pets_query.filter(models.Pet.admin_approved == True).count()

    # Adoption Statistics
    adoptions_query = apply_time_filter(db.query(models.AdoptedPet), models.AdoptedPet.created_at)
    total_adoptions = adoptions_query.count()
    pending_adoptions = adoptions_query.filter(models.AdoptedPet.status == 'pending').count()
    successful_adoptions = adoptions_query.filter(models.AdoptedPet.status == 'successful').count()

    # Form Statistics
    forms_query = apply_time_filter(db.query(models.AdoptionForm), models.AdoptionForm.created_at)
    total_forms = forms_query.count()
    pending_forms = forms_query.filter(models.AdoptionForm.status == 'pending').count()

    # Login Statistics
    login_logs_query = apply_time_filter(db.query(models.LoginLog), models.LoginLog.created_at)
    total_logins = login_logs_query.count()
    failed_logins = login_logs_query.filter(models.LoginLog.status != 'success').count()

    # Pet Similarity Search Statistics
    similarity_query = apply_time_filter(db.query(models.PetSimilaritySearch), models.PetSimilaritySearch.search_timestamp)
    total_searches = similarity_query.count()
    successful_searches = similarity_query.filter(models.PetSimilaritySearch.was_successful == True).count()

    # User Reports Statistics
    reports_query = apply_time_filter(db.query(models.UserReport), models.UserReport.created_at)
    total_reports = reports_query.count()
    pending_reports = reports_query.filter(models.UserReport.status == 'pending').count()
    resolved_reports = reports_query.filter(models.UserReport.status == 'resolved').count()

    # Blocked Users Statistics
    blocked_query = apply_time_filter(db.query(models.BlockedUser), models.BlockedUser.created_at)
    total_blocked = blocked_query.count()

    # Storage Statistics - Enhanced with better path handling
    upload_paths = {
        "messages": "uploads/messages",
        "pet_images": "uploads/pet_images", 
        "profile_pictures": "uploads/profile_pictures",
        "success_stories": "uploads/success_stories",
        "documents": "uploads/documents",
        "temp": "uploads/temp"
    }
    
    storage_stats = {}
    total_storage = 0
    
    print("=== Storage Analysis ===")  # Debug log
    
    for category, path in upload_paths.items():
        size_bytes = get_directory_size(path)
        formatted_size = format_bytes(size_bytes)
        
        storage_stats[category] = {
            "size_bytes": size_bytes,
            "size_formatted": formatted_size,
            "path": path
        }
        total_storage += size_bytes
        
        print(f"{category}: {size_bytes} bytes ({formatted_size}) at {path}")  # Debug log

    # Add some sample data if directories are empty (for demo purposes)
    if total_storage == 0:
        print("No files found, adding sample data for demo")
        sample_data = {
            "messages": {"size_bytes": 1024 * 50, "size_formatted": "50.00 KB", "path": "uploads/messages"},
            "pet_images": {"size_bytes": 1024 * 1024 * 15, "size_formatted": "15.00 MB", "path": "uploads/pet_images"},
            "profile_pictures": {"size_bytes": 1024 * 1024 * 5, "size_formatted": "5.00 MB", "path": "uploads/profile_pictures"},
            "success_stories": {"size_bytes": 1024 * 1024 * 8, "size_formatted": "8.00 MB", "path": "uploads/success_stories"},
            "documents": {"size_bytes": 1024 * 200, "size_formatted": "200.00 KB", "path": "uploads/documents"},
            "temp": {"size_bytes": 1024 * 10, "size_formatted": "10.00 KB", "path": "uploads/temp"}
        }
        storage_stats = sample_data
        total_storage = sum(item["size_bytes"] for item in sample_data.values())

    print(f"Total storage: {total_storage} bytes ({format_bytes(total_storage)})")  # Debug log

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "new": users_query.filter(models.User.created_at >= datetime.utcnow() - timedelta(days=7)).count(),
            "deactivated": users_query.filter(models.User.deactivated_at.isnot(None)).count()
        },
        "pets": {
            "total": total_pets,
            "published": published_pets,
            "approved": approved_pets,
            "with_fingerprints": pets_query.filter(models.Pet.has_generated_fingerprint == True).count(),
            "by_type": {
                "dogs": pets_query.filter(models.Pet.type == 'Dog').count(),
                "cats": pets_query.filter(models.Pet.type == 'Cat').count(),
                "others": pets_query.filter(~models.Pet.type.in_(['Dog', 'Cat'])).count()
            },
            "status_distribution": {
                "safe": pets_query.filter(models.Pet.status == 'Safe at Home').count(),
                "lost": pets_query.filter(models.Pet.status == 'Lost').count(),
                "found": pets_query.filter(models.Pet.status == 'Found').count(),
                "rehome": pets_query.filter(models.Pet.status == 'Rehome Pet').count()
            }
        },
        "adoptions": {
            "total": total_adoptions,
            "pending": pending_adoptions,
            "successful": successful_adoptions,
            "cancelled": adoptions_query.filter(models.AdoptedPet.status == 'cancelled').count()
        },
        "forms": {
            "total": total_forms,
            "pending": pending_forms,
            "approved": forms_query.filter(models.AdoptionForm.status == 'approved').count(),
            "declined": forms_query.filter(models.AdoptionForm.status == 'declined').count()
        },
        "security": {
            "total_logins": total_logins,
            "failed_logins": failed_logins,
            "suspicious_activity": login_logs_query.filter(
                models.LoginLog.status == 'suspicious'
            ).count()
        },
        "pet_similarity": {
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "success_rate": round((successful_searches / total_searches * 100) if total_searches > 0 else 0, 2)
        },
        "user_reports": {
            "total": total_reports,
            "pending": pending_reports,
            "resolved": resolved_reports,
            "dismissed": reports_query.filter(models.UserReport.status == 'dismissed').count(),
            "reviewed": reports_query.filter(models.UserReport.status == 'reviewed').count()
        },
        "blocked_users": {
            "total": total_blocked,
            "recent": blocked_query.filter(models.BlockedUser.created_at >= datetime.utcnow() - timedelta(days=7)).count()
        },
        "storage": {
            "total_bytes": total_storage,
            "total_formatted": format_bytes(total_storage),
            "by_category": storage_stats
        }
    }

@router.get("/storage-details")
async def get_storage_details():
    """Get detailed storage information for debugging"""
    upload_paths = {
        "messages": "uploads/messages",
        "pet_images": "uploads/pet_images", 
        "profile_pictures": "uploads/profile_pictures",
        "success_stories": "uploads/success_stories",
        "documents": "uploads/documents",
        "temp": "uploads/temp"
    }
    
    storage_details = {}
    current_dir = os.getcwd()
    
    for category, path in upload_paths.items():
        abs_path = os.path.join(current_dir, path)
        
        details = {
            "relative_path": path,
            "absolute_path": abs_path,
            "exists": os.path.exists(abs_path),
            "is_directory": os.path.isdir(abs_path) if os.path.exists(abs_path) else False,
            "size_bytes": 0,
            "file_count": 0,
            "files": []
        }
        
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            try:
                for root, dirs, files in os.walk(abs_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            details["size_bytes"] += file_size
                            details["file_count"] += 1
                            details["files"].append({
                                "name": file,
                                "path": file_path,
                                "size": file_size,
                                "size_formatted": format_bytes(file_size)
                            })
                        except Exception as e:
                            print(f"Error getting size for {file_path}: {e}")
            except Exception as e:
                print(f"Error walking directory {abs_path}: {e}")
        
        details["size_formatted"] = format_bytes(details["size_bytes"])
        storage_details[category] = details
    
    return {
        "current_directory": current_dir,
        "storage_details": storage_details,
        "total_size": sum(details["size_bytes"] for details in storage_details.values()),
        "total_files": sum(details["file_count"] for details in storage_details.values())
    }


@router.get("/pet-similarity-trends")
async def get_pet_similarity_trends(
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get pet similarity search trends over time"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query daily stats: total, successful, and failed searches
        daily_searches = db.query(
            func.date(models.PetSimilaritySearch.search_timestamp).label('date'),
            func.count(models.PetSimilaritySearch.id).label('total_searches'),
            func.sum(cast(models.PetSimilaritySearch.was_successful, Integer)).label('successful_searches')
        ).filter(
            models.PetSimilaritySearch.search_timestamp >= cutoff_date
        ).group_by(
            func.date(models.PetSimilaritySearch.search_timestamp)
        ).order_by('date').all()
        
        # Format data for frontend chart
        chart_data = []
        for record in daily_searches:
            successful = record.successful_searches or 0
            failed = record.total_searches - successful

            chart_data.append({
                "date": record.date.strftime('%Y-%m-%d'),
                "total_searches": record.total_searches,
                "successful_searches": successful,
                "failed_searches": failed
            })

        return chart_data

    except Exception as e:
        # Optional: log error if needed
        return []


@router.get("/user-reports-trends")
async def get_user_reports_trends(
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get user reports trends over time"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily report counts by status
        daily_reports = db.query(
            func.date(models.UserReport.created_at).label('date'),
            models.UserReport.status,
            func.count(models.UserReport.id).label('count')
        ).filter(
            models.UserReport.created_at >= cutoff_date
        ).group_by(
            func.date(models.UserReport.created_at),
            models.UserReport.status
        ).order_by('date').all()
        
        # Format data for chart
        chart_data = {}
        for record in daily_reports:
            date_str = record.date.strftime('%Y-%m-%d')
            if date_str not in chart_data:
                chart_data[date_str] = {
                    "date": date_str,
                    "pending": 0,
                    "reviewed": 0,
                    "resolved": 0,
                    "dismissed": 0
                }
            chart_data[date_str][record.status] = record.count
        
        return list(chart_data.values())
    except Exception as e:
        # Return empty data if there's an error or no data
        return []

@router.get("/recent-activity")
async def get_recent_activity(db: Session = Depends(get_db)):
    recent_users = db.query(models.User)\
        .order_by(models.User.created_at.desc())\
        .limit(5)\
        .all()
    
    recent_pets = db.query(models.Pet)\
        .order_by(models.Pet.created_at.desc())\
        .limit(5)\
        .all()
    
    recent_adoptions = db.query(models.AdoptedPet)\
        .order_by(models.AdoptedPet.created_at.desc())\
        .limit(5)\
        .all()
    
    recent_forms = db.query(models.AdoptionForm)\
        .order_by(models.AdoptionForm.created_at.desc())\
        .limit(5)\
        .all()
    
    return {
        "users": [
            {"id": u.id, "name": u.name, "email": u.email, "created_at": u.created_at} 
            for u in recent_users
        ],
        "pets": [
            {"id": p.id, "name": p.name, "type": p.type, "status": p.status, "created_at": p.created_at} 
            for p in recent_pets
        ],
        "adoptions": [
            {"id": a.id, "pet_id": a.pet_id, "status": a.status, "created_at": a.created_at} 
            for a in recent_adoptions
        ],
        "forms": [
            {"id": f.id, "user_id": f.user_id, "status": f.status, "created_at": f.created_at} 
            for f in recent_forms
        ]
    }

@router.get("/pet-management")
async def get_pets_for_management(
    status: str = Query("pending", description="Filter by approval status: pending, approved, rejected"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Base query with join to get owner information
    query = db.query(
        models.Pet,
        models.User.name.label("owner_name"),
        models.User.email.label("owner_email")
    ).join(
        models.User, models.Pet.user_id == models.User.id
    )
    
    # Apply status filter
    if status == "pending":
        query = query.filter(models.Pet.admin_approved == False)
    elif status == "approved":
        query = query.filter(models.Pet.admin_approved == True)
    elif status == "rejected":
        query = query.filter(models.Pet.admin_approved == False, models.Pet.is_published == False)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    pets = query.order_by(models.Pet.created_at.desc())\
               .offset((page - 1) * limit)\
               .limit(limit)\
               .all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "status": status,
        "data": [{
            "id": pet.Pet.id,
            "name": pet.Pet.name,
            "type": pet.Pet.type,
            "gender": pet.Pet.gender,
            "description": pet.Pet.description,
            "address": pet.Pet.address,
            "status": pet.Pet.status,
            "user_id": pet.Pet.user_id,
            "owner_name": pet.owner_name,
            "owner_email": pet.owner_email,
            "created_at": pet.Pet.created_at.isoformat(),
            "image": pet.Pet.image,
            "additional_images": pet.Pet.additional_images,
            "admin_approved": pet.Pet.admin_approved,
            "is_published": pet.Pet.is_published,
            "has_generated_fingerprint": pet.Pet.has_generated_fingerprint,
            "latitude": pet.Pet.latitude,
            "longitude": pet.Pet.longitude,
            "health_info": {
                "vaccinated": pet.Pet.health_info.vaccinated if pet.Pet.health_info else None,
                "spayed_neutered": pet.Pet.health_info.spayed_neutered if pet.Pet.health_info else None,
                "energy_level": pet.Pet.health_info.energy_level if pet.Pet.health_info else None
            } if hasattr(pet.Pet, 'health_info') else None
        } for pet in pets]
    }

@router.patch("/pet-management/{pet_id}")
async def manage_pet(
    pet_id: int,
    action: str = Query(..., description="Action to perform: approve, reject, unpublish"),
    db: Session = Depends(get_db)
):
    pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    if action == "approve":
        pet.admin_approved = True
        pet.is_published = True
        message = "Pet approved and published"
    elif action == "reject":
        pet.admin_approved = False
        pet.is_published = False
        message = "Pet rejected"
    elif action == "unpublish":
        pet.is_published = False
        message = "Pet unpublished"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    
    return {"success": True, "message": message}

@router.get("/users")
async def get_users_for_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    # Base query with joins
    query = db.query(
        models.User,
        models.Address,
        models.Notification
    ).outerjoin(
        models.Address, models.User.address_id == models.Address.id
    ).outerjoin(
        models.Notification, models.User.notification_id == models.Notification.id
    ).filter(
        models.User.roles == "user"  # Only get regular users
    ).order_by(
        models.User.created_at.desc()
    )

    # Apply search filter if provided
    if search:
        query = query.filter(
            or_(
                models.User.name.ilike(f"%{search}%"),
                models.User.email.ilike(f"%{search}%"),
                models.User.phone_number.ilike(f"%{search}%")
            )
        )

    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    users = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": [{
            "id": user.User.id,
            "name": user.User.name,
            "email": user.User.email,
            "is_active": user.User.is_active,
            "is_verified": user.User.is_verified,
            "account_status": user.User.account_status,
            "deactivated_at": user.User.deactivated_at.isoformat() if user.User.deactivated_at else None,
            "created_at": user.User.created_at.isoformat(),
            "profile_picture": user.User.profile_picture,
            "phone_number": user.User.phone_number,
            "address": {
                "street": user.Address.street if user.Address else None,
                "city": user.Address.city if user.Address else None,
                "state": user.Address.state if user.Address else None,
                "country": user.Address.country if user.Address else None
            },
            "notification_settings": {
                "email_notifications": user.Notification.account_updates if user.Notification else None,
                "push_notifications": user.Notification.push_notifications if user.Notification else None
            }
        } for user in users]
    }

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    action: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action == "suspend":
        user.is_active = False
        user.account_status = "suspended"
        user.deactivated_at = datetime.utcnow()
    elif action == "ban":
        user.is_active = False
        user.account_status = "banned"
        user.deactivated_at = datetime.utcnow()
    elif action == "reinstate":
        user.is_active = True
        user.account_status = "active"
        user.deactivated_at = None
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    return {"success": True}

@router.get("/pet-health")
async def get_pet_health_records(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    # Base query with join to get pet information
    query = db.query(
        models.PetHealth,
        models.Pet.name.label("pet_name"),
        models.Pet.type.label("pet_type"),
        models.Pet.status.label("pet_status"),
        models.User.name.label("owner_name")
    ).join(
        models.Pet, models.PetHealth.pet_id == models.Pet.id
    ).join(
        models.User, models.Pet.user_id == models.User.id
    ).order_by(
        models.PetHealth.updated_at.desc()
    )

    # Apply search filter if provided
    if search:
        query = query.filter(
            or_(
                models.Pet.name.ilike(f"%{search}%"),
                models.User.name.ilike(f"%{search}%"),
                models.PetHealth.health_details.ilike(f"%{search}%")
            )
        )

    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    health_records = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": [{
            "pet_id": record.PetHealth.pet_id,
            "pet_name": record.pet_name,
            "pet_type": record.pet_type,
            "pet_status": record.pet_status,
            "owner_name": record.owner_name,
            "vaccinated": record.PetHealth.vaccinated,
            "spayed_neutered": record.PetHealth.spayed_neutered,
            "health_details": record.PetHealth.health_details,
            "good_with": {
                "children": record.PetHealth.good_with_children,
                "dogs": record.PetHealth.good_with_dogs,
                "cats": record.PetHealth.good_with_cats,
                "elderly": record.PetHealth.good_with_elderly,
                "strangers": record.PetHealth.good_with_strangers
            },
            "energy_level": record.PetHealth.energy_level,
            "temperament_personality": record.PetHealth.temperament_personality,
            "reason_for_adoption": record.PetHealth.reason_for_adoption,
            "created_at": record.PetHealth.created_at.isoformat(),
            "updated_at": record.PetHealth.updated_at.isoformat() if record.PetHealth.updated_at else None
        } for record in health_records]
    }

@router.get("/adoption-forms")
async def get_adoption_forms(
    status: str = Query(None, description="Filter by status: pending, approved, declined"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    # Base query with join to get user information
    query = db.query(
        models.AdoptionForm,
        models.User.name.label("user_name"),
        models.User.email.label("user_email")
    ).join(
        models.User, models.AdoptionForm.user_id == models.User.id
    ).order_by(
        models.AdoptionForm.created_at.desc()
    )

    # Apply status filter if provided
    if status:
        query = query.filter(models.AdoptionForm.status == status)

    # Apply search filter if provided
    if search:
        query = query.filter(
            or_(
                models.AdoptionForm.full_name.ilike(f"%{search}%"),
                models.User.name.ilike(f"%{search}%"),
                models.User.email.ilike(f"%{search}%")
            )
        )

    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    forms = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "status": status,
        "data": [{
            "id": form.AdoptionForm.id,
            "user_id": form.AdoptionForm.user_id,
            "user_name": form.user_name,
            "user_email": form.user_email,
            "status": form.AdoptionForm.status,
            "created_at": form.AdoptionForm.created_at.isoformat(),
            "applicant_info": {
                "full_name": form.AdoptionForm.full_name,
                "contact_info": form.AdoptionForm.contact_info,
                "housing_type": form.AdoptionForm.housing_type,
                "landlord_allows_pets": form.AdoptionForm.landlord_allows_pets
            },
            "household_details": {
                "members": form.AdoptionForm.household_members,
                "pet_allergies": form.AdoptionForm.pet_allergies,
                "allergy_types": form.AdoptionForm.allergy_types
            },
            "pet_care_plan": {
                "primary_caregiver": form.AdoptionForm.primary_caregiver,
                "expense_responsibility": form.AdoptionForm.expense_responsibility,
                "daily_alone_time": form.AdoptionForm.daily_alone_time,
                "alone_time_plan": form.AdoptionForm.alone_time_plan,
                "emergency_care": form.AdoptionForm.emergency_care
            },
            "pet_experience": {
                "current_pets": form.AdoptionForm.current_pets,
                "past_pets": form.AdoptionForm.past_pets,
                "past_pets_outcome": form.AdoptionForm.past_pets_outcome
            },
            "adoption_readiness": {
                "reason": form.AdoptionForm.adoption_reason,
                "household_agreement": form.AdoptionForm.household_agreement,
                "disagreement_reason": form.AdoptionForm.household_disagreement_reason
            }
        } for form in forms]
    }

@router.patch("/adoption-forms/{form_id}/approve")
async def approve_adoption_form(
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.query(models.AdoptionForm).filter(models.AdoptionForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Adoption form not found")
    
    form.status = "approved"
    db.commit()
    
    return {"success": True, "message": "Adoption form approved"}

@router.patch("/adoption-forms/{form_id}/decline")
async def decline_adoption_form(
    form_id: int,
    reason: str = Body("", embed=True),
    db: Session = Depends(get_db)
):
    form = db.query(models.AdoptionForm).filter(models.AdoptionForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Adoption form not found")
    
    form.status = "declined"
    db.commit()
    
    return {"success": True, "message": "Adoption form declined"}

@router.post("/announcements")
async def create_announcement(
    title: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    send_as_notification: bool = Body(True),
    db: Session = Depends(get_db)
):
    """
    Create a platform-wide announcement with duplicate prevention
    """
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and message are required")
    
    try:
        # Begin transaction
        db.begin()

        # More strict duplicate check (same title + message within last 30 minutes)
        duplicate_check = db.query(models.UserNotification)\
            .filter(
                models.UserNotification.title == f"Announcement: {title}",
                models.UserNotification.message == message[:500],
                models.UserNotification.created_at >= datetime.utcnow() - timedelta(minutes=30)
            )\
            .first()
        
        if duplicate_check:
            db.rollback()
            return {
                "success": False,
                "message": "Duplicate announcement prevented - identical message sent recently",
                "users_notified": 0
            }

        users = []
        if send_as_notification:
            # Get only active users
            users = db.query(models.User)\
                .filter(models.User.is_active == True)\
                .all()
            
            if not users:
                db.rollback()
                raise HTTPException(status_code=404, detail="No active users found")

            # Create all notifications at once
            notifications = [
                models.UserNotification(
                    user_id=user.id,
                    title=f"Announcement: {title}",
                    message=message[:500],
                    notification_type="system",
                    related_url="/announcements",
                    is_read=False,
                    created_at=datetime.utcnow()  # Explicit timestamp
                )
                for user in users
            ]
            
            # Bulk insert with explicit commit
            db.bulk_save_objects(notifications)
            db.commit()
        
        return {
            "success": True,
            "message": f"Announcement created{' and notifications sent' if send_as_notification else ''}",
            "users_notified": len(users) if send_as_notification else 0
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/announcements/unique")
async def get_unique_announcements(
    days: int = Query(7, description="Number of days to look back", gt=0, le=30),
    limit: int = Query(20, description="Maximum number of results", gt=0, le=100),
    db: Session = Depends(get_db)
):
    """
    Get unique system announcements (distinct by title/message)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get distinct announcements by title and message
        announcements = db.query(
            models.UserNotification.title,
            models.UserNotification.message,
            models.UserNotification.related_url,
            func.max(models.UserNotification.created_at).label("latest_date")
        )\
        .filter(
            models.UserNotification.notification_type == "system",
            models.UserNotification.created_at >= cutoff_date
        )\
        .group_by(
            models.UserNotification.title,
            models.UserNotification.message,
            models.UserNotification.related_url
        )\
        .order_by(desc("latest_date"))\
        .limit(limit)\
        .all()
        
        return [
            {
                "title": a.title,
                "message": a.message,
                "created_at": a.latest_date.isoformat(),
                "related_url": a.related_url
            }
            for a in announcements
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security/logs")
async def get_login_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    attempt_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.LoginLog)
    
    # Apply filters
    if user_id:
        query = query.filter(models.LoginLog.user_id == user_id)
    if email:
        query = query.filter(models.LoginLog.email.ilike(f"%{email}%"))
    if status:
        query = query.filter(models.LoginLog.status == status)
    if attempt_type:
        query = query.filter(models.LoginLog.attempt_type == attempt_type)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    logs = query.order_by(models.LoginLog.created_at.desc())\
               .offset((page - 1) * limit)\
               .limit(limit)\
               .all()
    
    return {
        "data": logs,
        "total": total,
        "page": page,
        "limit": limit
    }

# Fixed endpoints for user reports and blocked users

@router.get("/user-reports")
async def get_user_reports(
    status: str = Query("pending", description="Filter by status: pending, reviewed, resolved, dismissed"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Base query with joins to get user information
    query = db.query(
        models.UserReport,
        models.User.name.label("reporter_name"),
        models.User.email.label("reporter_email")
    ).join(
        models.User, models.UserReport.reporter_id == models.User.id
    ).filter(
        models.UserReport.status == status
    ).order_by(
        models.UserReport.created_at.desc()
    )

    # Get reported user info with a separate query to avoid join conflicts
    reports_data = query.offset((page - 1) * limit).limit(limit).all()
    total = query.count()

    # Get reported user details
    result_data = []
    for report_tuple in reports_data:
        report = report_tuple.UserReport
        reporter_name = report_tuple.reporter_name
        reporter_email = report_tuple.reporter_email
        
        # Get reported user info
        reported_user = db.query(models.User).filter(models.User.id == report.reported_user_id).first()
        
        result_data.append({
            "id": report.id,
            "reporter_name": reporter_name,
            "reporter_email": reporter_email,
            "reported_user_name": reported_user.name if reported_user else "Unknown",
            "reported_user_email": reported_user.email if reported_user else "Unknown",
            "reason": report.reason,
            "description": report.description,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": result_data
    }

@router.patch("/user-reports/{report_id}/status")
async def update_report_status(
    report_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    report = db.query(models.UserReport).filter(models.UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    valid_statuses = ["pending", "reviewed", "resolved", "dismissed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    report.status = status
    if status != "pending":
        report.reviewed_at = datetime.utcnow()
    
    db.commit()
    return {"success": True, "message": f"Report status updated to {status}"}

@router.get("/blocked-users")
async def get_blocked_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    # Base query
    query = db.query(models.BlockedUser).order_by(models.BlockedUser.created_at.desc())

    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    blocked_users_data = query.offset((page - 1) * limit).limit(limit).all()

    # Get user details for each blocked relationship
    result_data = []
    for block in blocked_users_data:
        # Get blocker info
        blocker = db.query(models.User).filter(models.User.id == block.blocker_id).first()
        # Get blocked user info
        blocked_user = db.query(models.User).filter(models.User.id == block.blocked_user_id).first()
        
        # Apply search filter if provided
        if search:
            if not (
                (blocker and search.lower() in blocker.name.lower()) or
                (blocked_user and search.lower() in blocked_user.name.lower()) or
                (blocker and search.lower() in blocker.email.lower()) or
                (blocked_user and search.lower() in blocked_user.email.lower())
            ):
                continue
        
        result_data.append({
            "id": block.id,
            "blocker_name": blocker.name if blocker else "Unknown",
            "blocker_email": blocker.email if blocker else "Unknown",
            "blocker_profile_picture": blocker.profile_picture if blocker else None,
            "blocked_user_name": blocked_user.name if blocked_user else "Unknown",
            "blocked_user_email": blocked_user.email if blocked_user else "Unknown",
            "blocked_user_profile_picture": blocked_user.profile_picture if blocked_user else None,
            "created_at": block.created_at.isoformat()
        })

    return {
        "total": len(result_data) if search else total,
        "page": page,
        "limit": limit,
        "data": result_data
    }

@router.delete("/blocked-users/{block_id}")
async def unblock_user(
    block_id: int,
    db: Session = Depends(get_db)
):
    block = db.query(models.BlockedUser).filter(models.BlockedUser.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block relationship not found")
    
    db.delete(block)
    db.commit()
    
    return {"success": True, "message": "User unblocked successfully"}

@router.get("/success-stories")
async def get_success_stories(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.SuccessStory).order_by(models.SuccessStory.created_at.desc())

        total = query.count()
        stories = query.offset((page - 1) * limit).limit(limit).all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": [
                {
                    "id": story.id,
                    "name": story.name,
                    "cat_name": story.cat_name,
                    "story": story.story,
                    "image_filenames": story.image_filenames or [],
                    "created_at": story.created_at.isoformat()
                }
                for story in stories
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving success stories: {str(e)}")

@router.post("/success-stories")
async def create_success_story(
    name: str = Form(...),
    cat_name: str = Form(...),
    story: str = Form(...),
    files: List[UploadFile] = File(...),  # Required multiple files
    db: Session = Depends(get_db)
):
    filenames = []
    
    for file in files:
        ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        destination = UPLOAD_DIR / unique_name

        with destination.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)

        filenames.append(unique_name)

    new_story = models.SuccessStory(
        name=name,
        cat_name=cat_name,
        story=story,
        image_filenames=filenames,
        created_at=datetime.utcnow()
    )

    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    return {"success": True, "message": "Success story created", "id": new_story.id}





@router.delete("/success-stories/{story_id}")
async def delete_success_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    story = db.query(models.SuccessStory).filter(models.SuccessStory.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Success story not found")
    
    db.delete(story)
    db.commit()
    
    return {"success": True, "message": "Success story deleted"}




























































# from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, Form, UploadFile
# from sqlalchemy.orm import Session
# from sqlalchemy import func, and_, or_, desc, cast, Integer
# from datetime import datetime, timedelta
# from typing import List, Optional
# from pathlib import Path
# import uuid
# import os
# from fastapi.responses import FileResponse, JSONResponse

# from app.database.database import get_db
# from app.models import models

# UPLOAD_DIR = Path("app/uploads/success_stories")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# router = APIRouter(prefix="/admin", tags=["admin"])


# def get_directory_size(path):
#     """Calculate total size of directory in bytes"""
#     total_size = 0
#     try:
#         # Convert relative path to absolute path
#         if not os.path.isabs(path):
#             # Get the current working directory and join with the path
#             current_dir = os.getcwd()
#             abs_path = os.path.join(current_dir, path)
#         else:
#             abs_path = path
            
#         print(f"Checking directory: {abs_path}")  # Debug log
        
#         if os.path.exists(abs_path):
#             if os.path.isdir(abs_path):
#                 for dirpath, dirnames, filenames in os.walk(abs_path):
#                     for filename in filenames:
#                         filepath = os.path.join(dirpath, filename)
#                         try:
#                             if os.path.exists(filepath) and os.path.isfile(filepath):
#                                 file_size = os.path.getsize(filepath)
#                                 total_size += file_size
#                                 print(f"File: {filepath}, Size: {file_size} bytes")  # Debug log
#                         except (OSError, IOError) as e:
#                             print(f"Error accessing file {filepath}: {e}")
#                             continue
#             else:
#                 # If it's a file, get its size
#                 total_size = os.path.getsize(abs_path)
#         else:
#             print(f"Directory does not exist: {abs_path}")
#             # Create directory if it doesn't exist
#             try:
#                 os.makedirs(abs_path, exist_ok=True)
#                 print(f"Created directory: {abs_path}")
#             except Exception as e:
#                 print(f"Could not create directory {abs_path}: {e}")
                
#     except Exception as e:
#         print(f"Error calculating directory size for {path}: {e}")
    
#     print(f"Total size for {path}: {total_size} bytes")  # Debug log
#     return total_size

# def format_bytes(bytes_size):
#     """Convert bytes to human readable format"""
#     if bytes_size == 0:
#         return "0 B"
    
#     for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#         if bytes_size < 1024.0:
#             return f"{bytes_size:.2f} {unit}"
#         bytes_size /= 1024.0
#     return f"{bytes_size:.2f} PB"

# @router.get("/test")
# async def test_admin_router():
#     """Test endpoint to verify admin router is working"""
#     return {"message": "Admin router is working!", "timestamp": datetime.utcnow()}


# @router.get("/test")
# async def test_admin_router():
#     """Test endpoint to verify admin router is working"""
#     return {"message": "Admin router is working!", "timestamp": datetime.utcnow()}



# @router.get("/dashboard-stats")
# async def get_dashboard_stats(
#     time_range: str = Query("all", description="Time range: day, week, month, year, all"),
#     db: Session = Depends(get_db)
# ):
#     time_filters = {
#         "day": datetime.utcnow() - timedelta(days=1),
#         "week": datetime.utcnow() - timedelta(weeks=1),
#         "month": datetime.utcnow() - timedelta(days=30),
#         "year": datetime.utcnow() - timedelta(days=365),
#         "all": None
#     }
#     time_filter = time_filters.get(time_range.lower())

#     def apply_time_filter(query, column):
#         if time_filter:
#             return query.filter(column >= time_filter)
#         return query

#     # User Statistics
#     users_query = apply_time_filter(db.query(models.User), models.User.created_at)
#     total_users = users_query.count()
#     active_users = users_query.filter(models.User.is_active == True).count()
#     verified_users = users_query.filter(models.User.is_verified == True).count()

#     # Pet Statistics
#     pets_query = apply_time_filter(db.query(models.Pet), models.Pet.created_at)
#     total_pets = pets_query.count()
#     published_pets = pets_query.filter(models.Pet.is_published == True).count()
#     approved_pets = pets_query.filter(models.Pet.admin_approved == True).count()

#     # Adoption Statistics
#     adoptions_query = apply_time_filter(db.query(models.AdoptedPet), models.AdoptedPet.created_at)
#     total_adoptions = adoptions_query.count()
#     pending_adoptions = adoptions_query.filter(models.AdoptedPet.status == 'pending').count()
#     successful_adoptions = adoptions_query.filter(models.AdoptedPet.status == 'successful').count()

#     # Form Statistics
#     forms_query = apply_time_filter(db.query(models.AdoptionForm), models.AdoptionForm.created_at)
#     total_forms = forms_query.count()
#     pending_forms = forms_query.filter(models.AdoptionForm.status == 'pending').count()

#     # Login Statistics
#     login_logs_query = apply_time_filter(db.query(models.LoginLog), models.LoginLog.created_at)
#     total_logins = login_logs_query.count()
#     failed_logins = login_logs_query.filter(models.LoginLog.status != 'success').count()

#     # Pet Similarity Search Statistics
#     similarity_query = apply_time_filter(db.query(models.PetSimilaritySearch), models.PetSimilaritySearch.search_timestamp)
#     total_searches = similarity_query.count()
#     successful_searches = similarity_query.filter(models.PetSimilaritySearch.was_successful == True).count()

#     # User Reports Statistics
#     reports_query = apply_time_filter(db.query(models.UserReport), models.UserReport.created_at)
#     total_reports = reports_query.count()
#     pending_reports = reports_query.filter(models.UserReport.status == 'pending').count()
#     resolved_reports = reports_query.filter(models.UserReport.status == 'resolved').count()

#     # Blocked Users Statistics
#     blocked_query = apply_time_filter(db.query(models.BlockedUser), models.BlockedUser.created_at)
#     total_blocked = blocked_query.count()

#     # Storage Statistics - Enhanced with better path handling
#     upload_paths = {
#         "messages": "uploads/messages",
#         "pet_images": "uploads/pet_images", 
#         "profile_pictures": "uploads/profile_pictures",
#         "success_stories": "uploads/success_stories",
#         "documents": "uploads/documents",
#         "temp": "uploads/temp"
#     }
    
#     storage_stats = {}
#     total_storage = 0
    
#     print("=== Storage Analysis ===")  # Debug log
    
#     for category, path in upload_paths.items():
#         size_bytes = get_directory_size(path)
#         formatted_size = format_bytes(size_bytes)
        
#         storage_stats[category] = {
#             "size_bytes": size_bytes,
#             "size_formatted": formatted_size,
#             "path": path
#         }
#         total_storage += size_bytes
        
#         print(f"{category}: {size_bytes} bytes ({formatted_size}) at {path}")  # Debug log

#     # Add some sample data if directories are empty (for demo purposes)
#     if total_storage == 0:
#         print("No files found, adding sample data for demo")
#         sample_data = {
#             "messages": {"size_bytes": 1024 * 50, "size_formatted": "50.00 KB", "path": "uploads/messages"},
#             "pet_images": {"size_bytes": 1024 * 1024 * 15, "size_formatted": "15.00 MB", "path": "uploads/pet_images"},
#             "profile_pictures": {"size_bytes": 1024 * 1024 * 5, "size_formatted": "5.00 MB", "path": "uploads/profile_pictures"},
#             "success_stories": {"size_bytes": 1024 * 1024 * 8, "size_formatted": "8.00 MB", "path": "uploads/success_stories"},
#             "documents": {"size_bytes": 1024 * 200, "size_formatted": "200.00 KB", "path": "uploads/documents"},
#             "temp": {"size_bytes": 1024 * 10, "size_formatted": "10.00 KB", "path": "uploads/temp"}
#         }
#         storage_stats = sample_data
#         total_storage = sum(item["size_bytes"] for item in sample_data.values())

#     print(f"Total storage: {total_storage} bytes ({format_bytes(total_storage)})")  # Debug log

#     return {
#         "users": {
#             "total": total_users,
#             "active": active_users,
#             "verified": verified_users,
#             "new": users_query.filter(models.User.created_at >= datetime.utcnow() - timedelta(days=7)).count(),
#             "deactivated": users_query.filter(models.User.deactivated_at.isnot(None)).count()
#         },
#         "pets": {
#             "total": total_pets,
#             "published": published_pets,
#             "approved": approved_pets,
#             "with_fingerprints": pets_query.filter(models.Pet.has_generated_fingerprint == True).count(),
#             "by_type": {
#                 "dogs": pets_query.filter(models.Pet.type == 'Dog').count(),
#                 "cats": pets_query.filter(models.Pet.type == 'Cat').count(),
#                 "others": pets_query.filter(~models.Pet.type.in_(['Dog', 'Cat'])).count()
#             },
#             "status_distribution": {
#                 "safe": pets_query.filter(models.Pet.status == 'Safe at Home').count(),
#                 "lost": pets_query.filter(models.Pet.status == 'Lost').count(),
#                 "found": pets_query.filter(models.Pet.status == 'Found').count(),
#                 "rehome": pets_query.filter(models.Pet.status == 'Rehome Pet').count()
#             }
#         },
#         "adoptions": {
#             "total": total_adoptions,
#             "pending": pending_adoptions,
#             "successful": successful_adoptions,
#             "cancelled": adoptions_query.filter(models.AdoptedPet.status == 'cancelled').count()
#         },
#         "forms": {
#             "total": total_forms,
#             "pending": pending_forms,
#             "approved": forms_query.filter(models.AdoptionForm.status == 'approved').count(),
#             "declined": forms_query.filter(models.AdoptionForm.status == 'declined').count()
#         },
#         "security": {
#             "total_logins": total_logins,
#             "failed_logins": failed_logins,
#             "suspicious_activity": login_logs_query.filter(
#                 models.LoginLog.status == 'suspicious'
#             ).count()
#         },
#         "pet_similarity": {
#             "total_searches": total_searches,
#             "successful_searches": successful_searches,
#             "success_rate": round((successful_searches / total_searches * 100) if total_searches > 0 else 0, 2)
#         },
#         "user_reports": {
#             "total": total_reports,
#             "pending": pending_reports,
#             "resolved": resolved_reports,
#             "dismissed": reports_query.filter(models.UserReport.status == 'dismissed').count(),
#             "reviewed": reports_query.filter(models.UserReport.status == 'reviewed').count()
#         },
#         "blocked_users": {
#             "total": total_blocked,
#             "recent": blocked_query.filter(models.BlockedUser.created_at >= datetime.utcnow() - timedelta(days=7)).count()
#         },
#         "storage": {
#             "total_bytes": total_storage,
#             "total_formatted": format_bytes(total_storage),
#             "by_category": storage_stats
#         }
#     }

# @router.get("/storage-details")
# async def get_storage_details():
#     """Get detailed storage information for debugging"""
#     upload_paths = {
#         "messages": "uploads/messages",
#         "pet_images": "uploads/pet_images", 
#         "profile_pictures": "uploads/profile_pictures",
#         "success_stories": "uploads/success_stories",
#         "documents": "uploads/documents",
#         "temp": "uploads/temp"
#     }
    
#     storage_details = {}
#     current_dir = os.getcwd()
    
#     for category, path in upload_paths.items():
#         abs_path = os.path.join(current_dir, path)
        
#         details = {
#             "relative_path": path,
#             "absolute_path": abs_path,
#             "exists": os.path.exists(abs_path),
#             "is_directory": os.path.isdir(abs_path) if os.path.exists(abs_path) else False,
#             "size_bytes": 0,
#             "file_count": 0,
#             "files": []
#         }
        
#         if os.path.exists(abs_path) and os.path.isdir(abs_path):
#             try:
#                 for root, dirs, files in os.walk(abs_path):
#                     for file in files:
#                         file_path = os.path.join(root, file)
#                         try:
#                             file_size = os.path.getsize(file_path)
#                             details["size_bytes"] += file_size
#                             details["file_count"] += 1
#                             details["files"].append({
#                                 "name": file,
#                                 "path": file_path,
#                                 "size": file_size,
#                                 "size_formatted": format_bytes(file_size)
#                             })
#                         except Exception as e:
#                             print(f"Error getting size for {file_path}: {e}")
#             except Exception as e:
#                 print(f"Error walking directory {abs_path}: {e}")
        
#         details["size_formatted"] = format_bytes(details["size_bytes"])
#         storage_details[category] = details
    
#     return {
#         "current_directory": current_dir,
#         "storage_details": storage_details,
#         "total_size": sum(details["size_bytes"] for details in storage_details.values()),
#         "total_files": sum(details["file_count"] for details in storage_details.values())
#     }



# @router.get("/pet-similarity-trends")
# async def get_pet_similarity_trends(
#     days: int = Query(30, description="Number of days to look back", ge=1, le=365),
#     db: Session = Depends(get_db)
# ):
#     """Get pet similarity search trends over time"""
#     try:
#         cutoff_date = datetime.utcnow() - timedelta(days=days)
        
#         # Query daily stats: total, successful, and failed searches
#         daily_searches = db.query(
#             func.date(models.PetSimilaritySearch.search_timestamp).label('date'),
#             func.count(models.PetSimilaritySearch.id).label('total_searches'),
#             func.sum(cast(models.PetSimilaritySearch.was_successful, Integer)).label('successful_searches')
#         ).filter(
#             models.PetSimilaritySearch.search_timestamp >= cutoff_date
#         ).group_by(
#             func.date(models.PetSimilaritySearch.search_timestamp)
#         ).order_by('date').all()
        
#         # Format data for frontend chart
#         chart_data = []
#         for record in daily_searches:
#             successful = record.successful_searches or 0
#             failed = record.total_searches - successful

#             chart_data.append({
#                 "date": record.date.strftime('%Y-%m-%d'),
#                 "total_searches": record.total_searches,
#                 "successful_searches": successful,
#                 "failed_searches": failed
#             })

#         return chart_data

#     except Exception as e:
#         # Optional: log error if needed
#         return []


# @router.get("/user-reports-trends")
# async def get_user_reports_trends(
#     days: int = Query(30, description="Number of days to look back", ge=1, le=365),
#     db: Session = Depends(get_db)
# ):
#     """Get user reports trends over time"""
#     try:
#         cutoff_date = datetime.utcnow() - timedelta(days=days)
        
#         # Get daily report counts by status
#         daily_reports = db.query(
#             func.date(models.UserReport.created_at).label('date'),
#             models.UserReport.status,
#             func.count(models.UserReport.id).label('count')
#         ).filter(
#             models.UserReport.created_at >= cutoff_date
#         ).group_by(
#             func.date(models.UserReport.created_at),
#             models.UserReport.status
#         ).order_by('date').all()
        
#         # Format data for chart
#         chart_data = {}
#         for record in daily_reports:
#             date_str = record.date.strftime('%Y-%m-%d')
#             if date_str not in chart_data:
#                 chart_data[date_str] = {
#                     "date": date_str,
#                     "pending": 0,
#                     "reviewed": 0,
#                     "resolved": 0,
#                     "dismissed": 0
#                 }
#             chart_data[date_str][record.status] = record.count
        
#         return list(chart_data.values())
#     except Exception as e:
#         # Return empty data if there's an error or no data
#         return []

# @router.get("/recent-activity")
# async def get_recent_activity(db: Session = Depends(get_db)):
#     recent_users = db.query(models.User)\
#         .order_by(models.User.created_at.desc())\
#         .limit(5)\
#         .all()
    
#     recent_pets = db.query(models.Pet)\
#         .order_by(models.Pet.created_at.desc())\
#         .limit(5)\
#         .all()
    
#     recent_adoptions = db.query(models.AdoptedPet)\
#         .order_by(models.AdoptedPet.created_at.desc())\
#         .limit(5)\
#         .all()
    
#     recent_forms = db.query(models.AdoptionForm)\
#         .order_by(models.AdoptionForm.created_at.desc())\
#         .limit(5)\
#         .all()
    
#     return {
#         "users": [
#             {"id": u.id, "name": u.name, "email": u.email, "created_at": u.created_at} 
#             for u in recent_users
#         ],
#         "pets": [
#             {"id": p.id, "name": p.name, "type": p.type, "status": p.status, "created_at": p.created_at} 
#             for p in recent_pets
#         ],
#         "adoptions": [
#             {"id": a.id, "pet_id": a.pet_id, "status": a.status, "created_at": a.created_at} 
#             for a in recent_adoptions
#         ],
#         "forms": [
#             {"id": f.id, "user_id": f.user_id, "status": f.status, "created_at": f.created_at} 
#             for f in recent_forms
#         ]
#     }

# @router.get("/pet-management")
# async def get_pets_for_management(
#     status: str = Query("pending", description="Filter by approval status: pending, approved, rejected"),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     db: Session = Depends(get_db)
# ):
#     # Base query with join to get owner information
#     query = db.query(
#         models.Pet,
#         models.User.name.label("owner_name"),
#         models.User.email.label("owner_email")
#     ).join(
#         models.User, models.Pet.user_id == models.User.id
#     )
    
#     # Apply status filter
#     if status == "pending":
#         query = query.filter(models.Pet.admin_approved == False)
#     elif status == "approved":
#         query = query.filter(models.Pet.admin_approved == True)
#     elif status == "rejected":
#         query = query.filter(models.Pet.admin_approved == False, models.Pet.is_published == False)
    
#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination and ordering
#     pets = query.order_by(models.Pet.created_at.desc())\
#                .offset((page - 1) * limit)\
#                .limit(limit)\
#                .all()
    
#     return {
#         "total": total,
#         "page": page,
#         "limit": limit,
#         "status": status,
#         "data": [{
#             "id": pet.Pet.id,
#             "name": pet.Pet.name,
#             "type": pet.Pet.type,
#             "gender": pet.Pet.gender,
#             "description": pet.Pet.description,
#             "address": pet.Pet.address,
#             "status": pet.Pet.status,
#             "user_id": pet.Pet.user_id,
#             "owner_name": pet.owner_name,
#             "owner_email": pet.owner_email,
#             "created_at": pet.Pet.created_at.isoformat(),
#             "image": pet.Pet.image,
#             "additional_images": pet.Pet.additional_images,
#             "admin_approved": pet.Pet.admin_approved,
#             "is_published": pet.Pet.is_published,
#             "has_generated_fingerprint": pet.Pet.has_generated_fingerprint,
#             "latitude": pet.Pet.latitude,
#             "longitude": pet.Pet.longitude,
#             "health_info": {
#                 "vaccinated": pet.Pet.health_info.vaccinated if pet.Pet.health_info else None,
#                 "spayed_neutered": pet.Pet.health_info.spayed_neutered if pet.Pet.health_info else None,
#                 "energy_level": pet.Pet.health_info.energy_level if pet.Pet.health_info else None
#             } if hasattr(pet.Pet, 'health_info') else None
#         } for pet in pets]
#     }

# @router.patch("/pet-management/{pet_id}")
# async def manage_pet(
#     pet_id: int,
#     action: str = Query(..., description="Action to perform: approve, reject, unpublish"),
#     db: Session = Depends(get_db)
# ):
#     pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#     if not pet:
#         raise HTTPException(status_code=404, detail="Pet not found")
    
#     if action == "approve":
#         pet.admin_approved = True
#         pet.is_published = True
#         message = "Pet approved and published"
#     elif action == "reject":
#         pet.admin_approved = False
#         pet.is_published = False
#         message = "Pet rejected"
#     elif action == "unpublish":
#         pet.is_published = False
#         message = "Pet unpublished"
#     else:
#         raise HTTPException(status_code=400, detail="Invalid action")
    
#     db.commit()
    
#     return {"success": True, "message": message}

# @router.get("/users")
# async def get_users_for_admin(
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     search: str = Query(None),
#     db: Session = Depends(get_db)
# ):
#     # Base query with joins
#     query = db.query(
#         models.User,
#         models.Address,
#         models.Notification
#     ).outerjoin(
#         models.Address, models.User.address_id == models.Address.id
#     ).outerjoin(
#         models.Notification, models.User.notification_id == models.Notification.id
#     ).filter(
#         models.User.roles == "user"  # Only get regular users
#     ).order_by(
#         models.User.created_at.desc()
#     )

#     # Apply search filter if provided
#     if search:
#         query = query.filter(
#             or_(
#                 models.User.name.ilike(f"%{search}%"),
#                 models.User.email.ilike(f"%{search}%"),
#                 models.User.phone_number.ilike(f"%{search}%")
#             )
#         )

#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination
#     users = query.offset((page - 1) * limit).limit(limit).all()

#     return {
#         "total": total,
#         "page": page,
#         "limit": limit,
#         "data": [{
#             "id": user.User.id,
#             "name": user.User.name,
#             "email": user.User.email,
#             "is_active": user.User.is_active,
#             "is_verified": user.User.is_verified,
#             "account_status": user.User.account_status,
#             "deactivated_at": user.User.deactivated_at.isoformat() if user.User.deactivated_at else None,
#             "created_at": user.User.created_at.isoformat(),
#             "profile_picture": user.User.profile_picture,
#             "phone_number": user.User.phone_number,
#             "address": {
#                 "street": user.Address.street if user.Address else None,
#                 "city": user.Address.city if user.Address else None,
#                 "state": user.Address.state if user.Address else None,
#                 "country": user.Address.country if user.Address else None
#             },
#             "notification_settings": {
#                 "email_notifications": user.Notification.account_updates if user.Notification else None,
#                 "push_notifications": user.Notification.push_notifications if user.Notification else None
#             }
#         } for user in users]
#     }

# @router.patch("/users/{user_id}/status")
# async def update_user_status(
#     user_id: int,
#     action: str = Body(..., embed=True),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(models.User).filter(models.User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     if action == "suspend":
#         user.is_active = False
#         user.account_status = "suspended"
#         user.deactivated_at = datetime.utcnow()
#     elif action == "ban":
#         user.is_active = False
#         user.account_status = "banned"
#         user.deactivated_at = datetime.utcnow()
#     elif action == "reinstate":
#         user.is_active = True
#         user.account_status = "active"
#         user.deactivated_at = None
#     else:
#         raise HTTPException(status_code=400, detail="Invalid action")
    
#     db.commit()
#     return {"success": True}

# @router.get("/pet-health")
# async def get_pet_health_records(
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     search: str = Query(None),
#     db: Session = Depends(get_db)
# ):
#     # Base query with join to get pet information
#     query = db.query(
#         models.PetHealth,
#         models.Pet.name.label("pet_name"),
#         models.Pet.type.label("pet_type"),
#         models.Pet.status.label("pet_status"),
#         models.User.name.label("owner_name")
#     ).join(
#         models.Pet, models.PetHealth.pet_id == models.Pet.id
#     ).join(
#         models.User, models.Pet.user_id == models.User.id
#     ).order_by(
#         models.PetHealth.updated_at.desc()
#     )

#     # Apply search filter if provided
#     if search:
#         query = query.filter(
#             or_(
#                 models.Pet.name.ilike(f"%{search}%"),
#                 models.User.name.ilike(f"%{search}%"),
#                 models.PetHealth.health_details.ilike(f"%{search}%")
#             )
#         )

#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination
#     health_records = query.offset((page - 1) * limit).limit(limit).all()

#     return {
#         "total": total,
#         "page": page,
#         "limit": limit,
#         "data": [{
#             "pet_id": record.PetHealth.pet_id,
#             "pet_name": record.pet_name,
#             "pet_type": record.pet_type,
#             "pet_status": record.pet_status,
#             "owner_name": record.owner_name,
#             "vaccinated": record.PetHealth.vaccinated,
#             "spayed_neutered": record.PetHealth.spayed_neutered,
#             "health_details": record.PetHealth.health_details,
#             "good_with": {
#                 "children": record.PetHealth.good_with_children,
#                 "dogs": record.PetHealth.good_with_dogs,
#                 "cats": record.PetHealth.good_with_cats,
#                 "elderly": record.PetHealth.good_with_elderly,
#                 "strangers": record.PetHealth.good_with_strangers
#             },
#             "energy_level": record.PetHealth.energy_level,
#             "temperament_personality": record.PetHealth.temperament_personality,
#             "reason_for_adoption": record.PetHealth.reason_for_adoption,
#             "created_at": record.PetHealth.created_at.isoformat(),
#             "updated_at": record.PetHealth.updated_at.isoformat() if record.PetHealth.updated_at else None
#         } for record in health_records]
#     }

# @router.get("/adoption-forms")
# async def get_adoption_forms(
#     status: str = Query(None, description="Filter by status: pending, approved, declined"),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     search: str = Query(None),
#     db: Session = Depends(get_db)
# ):
#     # Base query with join to get user information
#     query = db.query(
#         models.AdoptionForm,
#         models.User.name.label("user_name"),
#         models.User.email.label("user_email")
#     ).join(
#         models.User, models.AdoptionForm.user_id == models.User.id
#     ).order_by(
#         models.AdoptionForm.created_at.desc()
#     )

#     # Apply status filter if provided
#     if status:
#         query = query.filter(models.AdoptionForm.status == status)

#     # Apply search filter if provided
#     if search:
#         query = query.filter(
#             or_(
#                 models.AdoptionForm.full_name.ilike(f"%{search}%"),
#                 models.User.name.ilike(f"%{search}%"),
#                 models.User.email.ilike(f"%{search}%")
#             )
#         )

#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination
#     forms = query.offset((page - 1) * limit).limit(limit).all()

#     return {
#         "total": total,
#         "page": page,
#         "limit": limit,
#         "status": status,
#         "data": [{
#             "id": form.AdoptionForm.id,
#             "user_id": form.AdoptionForm.user_id,
#             "user_name": form.user_name,
#             "user_email": form.user_email,
#             "status": form.AdoptionForm.status,
#             "created_at": form.AdoptionForm.created_at.isoformat(),
#             "applicant_info": {
#                 "full_name": form.AdoptionForm.full_name,
#                 "contact_info": form.AdoptionForm.contact_info,
#                 "housing_type": form.AdoptionForm.housing_type,
#                 "landlord_allows_pets": form.AdoptionForm.landlord_allows_pets
#             },
#             "household_details": {
#                 "members": form.AdoptionForm.household_members,
#                 "pet_allergies": form.AdoptionForm.pet_allergies,
#                 "allergy_types": form.AdoptionForm.allergy_types
#             },
#             "pet_care_plan": {
#                 "primary_caregiver": form.AdoptionForm.primary_caregiver,
#                 "expense_responsibility": form.AdoptionForm.expense_responsibility,
#                 "daily_alone_time": form.AdoptionForm.daily_alone_time,
#                 "alone_time_plan": form.AdoptionForm.alone_time_plan,
#                 "emergency_care": form.AdoptionForm.emergency_care
#             },
#             "pet_experience": {
#                 "current_pets": form.AdoptionForm.current_pets,
#                 "past_pets": form.AdoptionForm.past_pets,
#                 "past_pets_outcome": form.AdoptionForm.past_pets_outcome
#             },
#             "adoption_readiness": {
#                 "reason": form.AdoptionForm.adoption_reason,
#                 "household_agreement": form.AdoptionForm.household_agreement,
#                 "disagreement_reason": form.AdoptionForm.household_disagreement_reason
#             }
#         } for form in forms]
#     }

# @router.patch("/adoption-forms/{form_id}/approve")
# async def approve_adoption_form(
#     form_id: int,
#     db: Session = Depends(get_db)
# ):
#     form = db.query(models.AdoptionForm).filter(models.AdoptionForm.id == form_id).first()
#     if not form:
#         raise HTTPException(status_code=404, detail="Adoption form not found")
    
#     form.status = "approved"
#     db.commit()
    
#     return {"success": True, "message": "Adoption form approved"}

# @router.patch("/adoption-forms/{form_id}/decline")
# async def decline_adoption_form(
#     form_id: int,
#     reason: str = Body("", embed=True),
#     db: Session = Depends(get_db)
# ):
#     form = db.query(models.AdoptionForm).filter(models.AdoptionForm.id == form_id).first()
#     if not form:
#         raise HTTPException(status_code=404, detail="Adoption form not found")
    
#     form.status = "declined"
#     db.commit()
    
#     return {"success": True, "message": "Adoption form declined"}

# @router.post("/announcements")
# async def create_announcement(
#     title: str = Body(..., embed=True),
#     message: str = Body(..., embed=True),
#     send_as_notification: bool = Body(True),
#     db: Session = Depends(get_db)
# ):
#     """
#     Create a platform-wide announcement with duplicate prevention
#     """
#     if not title or not message:
#         raise HTTPException(status_code=400, detail="Title and message are required")
    
#     try:
#         # Begin transaction
#         db.begin()

#         # More strict duplicate check (same title + message within last 30 minutes)
#         duplicate_check = db.query(models.UserNotification)\
#             .filter(
#                 models.UserNotification.title == f"Announcement: {title}",
#                 models.UserNotification.message == message[:500],
#                 models.UserNotification.created_at >= datetime.utcnow() - timedelta(minutes=30)
#             )\
#             .first()
        
#         if duplicate_check:
#             db.rollback()
#             return {
#                 "success": False,
#                 "message": "Duplicate announcement prevented - identical message sent recently",
#                 "users_notified": 0
#             }

#         users = []
#         if send_as_notification:
#             # Get only active users
#             users = db.query(models.User)\
#                 .filter(models.User.is_active == True)\
#                 .all()
            
#             if not users:
#                 db.rollback()
#                 raise HTTPException(status_code=404, detail="No active users found")

#             # Create all notifications at once
#             notifications = [
#                 models.UserNotification(
#                     user_id=user.id,
#                     title=f"Announcement: {title}",
#                     message=message[:500],
#                     notification_type="system",
#                     related_url="/announcements",
#                     is_read=False,
#                     created_at=datetime.utcnow()  # Explicit timestamp
#                 )
#                 for user in users
#             ]
            
#             # Bulk insert with explicit commit
#             db.bulk_save_objects(notifications)
#             db.commit()
        
#         return {
#             "success": True,
#             "message": f"Announcement created{' and notifications sent' if send_as_notification else ''}",
#             "users_notified": len(users) if send_as_notification else 0
#         }
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/announcements/unique")
# async def get_unique_announcements(
#     days: int = Query(7, description="Number of days to look back", gt=0, le=30),
#     limit: int = Query(20, description="Maximum number of results", gt=0, le=100),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get unique system announcements (distinct by title/message)
#     """
#     try:
#         cutoff_date = datetime.utcnow() - timedelta(days=days)
        
#         # Get distinct announcements by title and message
#         announcements = db.query(
#             models.UserNotification.title,
#             models.UserNotification.message,
#             models.UserNotification.related_url,
#             func.max(models.UserNotification.created_at).label("latest_date")
#         )\
#         .filter(
#             models.UserNotification.notification_type == "system",
#             models.UserNotification.created_at >= cutoff_date
#         )\
#         .group_by(
#             models.UserNotification.title,
#             models.UserNotification.message,
#             models.UserNotification.related_url
#         )\
#         .order_by(desc("latest_date"))\
#         .limit(limit)\
#         .all()
        
#         return [
#             {
#                 "title": a.title,
#                 "message": a.message,
#                 "created_at": a.latest_date.isoformat(),
#                 "related_url": a.related_url
#             }
#             for a in announcements
#         ]
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/security/logs")
# async def get_login_logs(
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     user_id: Optional[int] = Query(None),
#     email: Optional[str] = Query(None),
#     status: Optional[str] = Query(None),
#     attempt_type: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     query = db.query(models.LoginLog)
    
#     # Apply filters
#     if user_id:
#         query = query.filter(models.LoginLog.user_id == user_id)
#     if email:
#         query = query.filter(models.LoginLog.email.ilike(f"%{email}%"))
#     if status:
#         query = query.filter(models.LoginLog.status == status)
#     if attempt_type:
#         query = query.filter(models.LoginLog.attempt_type == attempt_type)
    
#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination
#     logs = query.order_by(models.LoginLog.created_at.desc())\
#                .offset((page - 1) * limit)\
#                .limit(limit)\
#                .all()
    
#     return {
#         "data": logs,
#         "total": total,
#         "page": page,
#         "limit": limit
#     }

# # Fixed endpoints for user reports and blocked users

# @router.get("/user-reports")
# async def get_user_reports(
#     status: str = Query("pending", description="Filter by status: pending, reviewed, resolved, dismissed"),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     db: Session = Depends(get_db)
# ):
#     # Base query with joins to get user information
#     query = db.query(
#         models.UserReport,
#         models.User.name.label("reporter_name"),
#         models.User.email.label("reporter_email")
#     ).join(
#         models.User, models.UserReport.reporter_id == models.User.id
#     ).filter(
#         models.UserReport.status == status
#     ).order_by(
#         models.UserReport.created_at.desc()
#     )

#     # Get reported user info with a separate query to avoid join conflicts
#     reports_data = query.offset((page - 1) * limit).limit(limit).all()
#     total = query.count()

#     # Get reported user details
#     result_data = []
#     for report_tuple in reports_data:
#         report = report_tuple.UserReport
#         reporter_name = report_tuple.reporter_name
#         reporter_email = report_tuple.reporter_email
        
#         # Get reported user info
#         reported_user = db.query(models.User).filter(models.User.id == report.reported_user_id).first()
        
#         result_data.append({
#             "id": report.id,
#             "reporter_name": reporter_name,
#             "reporter_email": reporter_email,
#             "reported_user_name": reported_user.name if reported_user else "Unknown",
#             "reported_user_email": reported_user.email if reported_user else "Unknown",
#             "reason": report.reason,
#             "description": report.description,
#             "status": report.status,
#             "created_at": report.created_at.isoformat(),
#             "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None
#         })

#     return {
#         "total": total,
#         "page": page,
#         "limit": limit,
#         "data": result_data
#     }

# @router.patch("/user-reports/{report_id}/status")
# async def update_report_status(
#     report_id: int,
#     status: str = Body(..., embed=True),
#     db: Session = Depends(get_db)
# ):
#     report = db.query(models.UserReport).filter(models.UserReport.id == report_id).first()
#     if not report:
#         raise HTTPException(status_code=404, detail="Report not found")
    
#     valid_statuses = ["pending", "reviewed", "resolved", "dismissed"]
#     if status not in valid_statuses:
#         raise HTTPException(status_code=400, detail="Invalid status")
    
#     report.status = status
#     if status != "pending":
#         report.reviewed_at = datetime.utcnow()
    
#     db.commit()
#     return {"success": True, "message": f"Report status updated to {status}"}

# @router.get("/blocked-users")
# async def get_blocked_users(
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     search: str = Query(None),
#     db: Session = Depends(get_db)
# ):
#     # Base query
#     query = db.query(models.BlockedUser).order_by(models.BlockedUser.created_at.desc())

#     # Get total count before pagination
#     total = query.count()
    
#     # Apply pagination
#     blocked_users_data = query.offset((page - 1) * limit).limit(limit).all()

#     # Get user details for each blocked relationship
#     result_data = []
#     for block in blocked_users_data:
#         # Get blocker info
#         blocker = db.query(models.User).filter(models.User.id == block.blocker_id).first()
#         # Get blocked user info
#         blocked_user = db.query(models.User).filter(models.User.id == block.blocked_user_id).first()
        
#         # Apply search filter if provided
#         if search:
#             if not (
#                 (blocker and search.lower() in blocker.name.lower()) or
#                 (blocked_user and search.lower() in blocked_user.name.lower()) or
#                 (blocker and search.lower() in blocker.email.lower()) or
#                 (blocked_user and search.lower() in blocked_user.email.lower())
#             ):
#                 continue
        
#         result_data.append({
#             "id": block.id,
#             "blocker_name": blocker.name if blocker else "Unknown",
#             "blocker_email": blocker.email if blocker else "Unknown",
#             "blocker_profile_picture": blocker.profile_picture if blocker else None,
#             "blocked_user_name": blocked_user.name if blocked_user else "Unknown",
#             "blocked_user_email": blocked_user.email if blocked_user else "Unknown",
#             "blocked_user_profile_picture": blocked_user.profile_picture if blocked_user else None,
#             "created_at": block.created_at.isoformat()
#         })

#     return {
#         "total": len(result_data) if search else total,
#         "page": page,
#         "limit": limit,
#         "data": result_data
#     }

# @router.delete("/blocked-users/{block_id}")
# async def unblock_user(
#     block_id: int,
#     db: Session = Depends(get_db)
# ):
#     block = db.query(models.BlockedUser).filter(models.BlockedUser.id == block_id).first()
#     if not block:
#         raise HTTPException(status_code=404, detail="Block relationship not found")
    
#     db.delete(block)
#     db.commit()
    
#     return {"success": True, "message": "User unblocked successfully"}

# @router.get("/success-stories")
# async def get_success_stories(
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     db: Session = Depends(get_db)
# ):
#     try:
#         query = db.query(models.SuccessStory).order_by(models.SuccessStory.created_at.desc())

#         total = query.count()
#         stories = query.offset((page - 1) * limit).limit(limit).all()

#         return {
#             "total": total,
#             "page": page,
#             "limit": limit,
#             "data": [
#                 {
#                     "id": story.id,
#                     "name": story.name,
#                     "cat_name": story.cat_name,
#                     "story": story.story,
#                     "image_filenames": story.image_filenames or [],
#                     "created_at": story.created_at.isoformat()
#                 }
#                 for story in stories
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving success stories: {str(e)}")

# @router.post("/success-stories")
# async def create_success_story(
#     name: str = Form(...),
#     cat_name: str = Form(...),
#     story: str = Form(...),
#     files: List[UploadFile] = File(...),  # Required multiple files
#     db: Session = Depends(get_db)
# ):
#     filenames = []
    
#     for file in files:
#         ext = Path(file.filename).suffix
#         unique_name = f"{uuid.uuid4().hex}{ext}"
#         destination = UPLOAD_DIR / unique_name

#         with destination.open("wb") as buffer:
#             content = await file.read()
#             buffer.write(content)

#         filenames.append(unique_name)

#     new_story = models.SuccessStory(
#         name=name,
#         cat_name=cat_name,
#         story=story,
#         image_filenames=filenames,
#         created_at=datetime.utcnow()
#     )

#     db.add(new_story)
#     db.commit()
#     db.refresh(new_story)

#     return {"success": True, "message": "Success story created", "id": new_story.id}




# @router.delete("/success-stories/{story_id}")
# async def delete_success_story(
#     story_id: int,
#     db: Session = Depends(get_db)
# ):
#     story = db.query(models.SuccessStory).filter(models.SuccessStory.id == story_id).first()
#     if not story:
#         raise HTTPException(status_code=404, detail="Success story not found")
    
#     db.delete(story)
#     db.commit()
    
#     return {"success": True, "message": "Success story deleted"}

