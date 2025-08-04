# Pet router - Add your pet-related endpoints here
# # backend/app/routers/pet_router.py
# backend/app/routers/pet_router.py
# Pet router - Add your pet-related endpoints here
# # backend/app/routers/pet_router.py
# backend/app/routers/pet_router.py
from fastapi import APIRouter, HTTPException, Depends, status, Body, UploadFile, Query, File, Form
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
from fastapi.responses import JSONResponse
from geopy.distance import geodesic  # Install with: pip install geopy
from app.models.models import User
from typing import Dict, Optional
from app.models.models import PetSimilaritySearch
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from ..services.pet_detector import verify_pet_image
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.attributes import flag_modified
from ..models.models import Pet
from sqlalchemy import func

import os
import re
import uuid
from pathlib import Path
from PIL import Image
import io
import json

from supabase import create_client
import os
import uuid

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_PET_BUCKET", "pet-images")

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase initialized successfully")
except Exception as e:
    print(f"Supabase init failed: {str(e)}")
    raise RuntimeError("Supabase initialization failed") from e

# === TensorFlow conditional import ===
try:
    import tensorflow as tf
    from ..services.pet_feature_extractor import PetFeatureExtractor
    USE_TENSORFLOW = True
    feature_extractor = PetFeatureExtractor()
except ImportError:
    print("TensorFlow not available. Feature extraction is disabled.")
    USE_TENSORFLOW = False
    feature_extractor = None

# === Upload directory setup ===
UPLOAD_DIR = Path("app/uploads/pet_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist

router = APIRouter(prefix="/api/pets", tags=["pets"])
router.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")

# If you have old string path usage, keep for compatibility
UPLOAD_DIR = "app/uploads/pet_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)



# Add ONLY if needed ↓
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

@router.post("/")
async def create_pet(pet_data: dict, db: Session = Depends(get_db)):
    try:
        pet_date = datetime.strptime(pet_data["date"], "%Y-%m-%dT%H:%M")
        
        # Create the pet first to get the ID
        db_pet = models.Pet(
            name=pet_data["name"],
            type=pet_data.get("type", "Dog"),
            gender=pet_data.get("gender", "Male"),
            description=pet_data.get("description", ""),
            date=pet_date,
            address=pet_data.get("address", ""),
            status=pet_data.get("status", "Safe at Home"),
            image=None,  # Will be updated after we get the pet ID
            user_id=pet_data["user_id"],
            latitude=pet_data.get("latitude"),
            longitude=pet_data.get("longitude")
        )
        
        db.add(db_pet)
        db.commit()
        db.refresh(db_pet)

        # Now update the image path with the pet ID
        if pet_data.get("image"):
            # Construct the proper file path: pet_id/main.jpg
            image_path = f"{db_pet.id}/main.jpg"
            db_pet.image = image_path
            db.commit()
            db.refresh(db_pet)

        # Optional: Notify the pet owner ↓
        create_notification(
            db,
            pet_data["user_id"],
            "New Pet Added",
            f"{pet_data['name']} was registered successfully",
            "pet"
        )
        
        return {"message": "Pet saved successfully", "pet_id": db_pet.id}
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create pet: {str(e)}")











@router.post("/register-device", status_code=201)
async def register_device(device_data: dict, db: Session = Depends(get_db)):
    """
    Register a new pet tracking device
    Expects: {"unique_code": "string"}
    """
    try:
        # Validate input
        if not device_data.get("unique_code"):
            raise HTTPException(
                status_code=422,
                detail={"message": "unique_code is required"}
            )

        unique_code = device_data["unique_code"]  # Extract the string value

        # Check for existing device - including status check
        existing = db.query(models.Device).filter(
            models.Device.unique_code == unique_code,
            models.Device.status != "removed"  # Only consider non-removed devices
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail={"message": "Device already registered"}
            )
        
        # Create new device with status
        db_device = models.Device(
            unique_code=unique_code,
            is_active=False,
            is_online=False,
            status="working"  # Explicitly set status (default would work too)
        )
        
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        return {
            "status": "success",
            "message": "Device registered",
            "data": {
                "device_id": db_device.device_id,
                "unique_code": db_device.unique_code,
                "status": db_device.status  # Include status in response
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"message": f"Registration failed: {str(e)}"}
        )
    

@router.patch("/update-device-status/{device_id}", status_code=200)
async def update_device_status(
    device_id: int,
    status_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update device status
    Expects: {"status": "working" | "removed"}
    """
    try:
        if not status_data.get("status") or status_data["status"] not in ["working", "removed"]:
            raise HTTPException(
                status_code=422,
                detail={"message": "Valid status (working/removed) is required"}
            )

        device = db.query(models.Device).filter(
            models.Device.device_id == device_id
        ).first()

        if not device:
            raise HTTPException(
                status_code=404,
                detail={"message": "Device not found"}
            )

        device.status = status_data["status"]
        db.commit()
        
        return {
            "status": "success",
            "message": "Device status updated",
            "data": {
                "device_id": device.device_id,
                "new_status": device.status
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"message": f"Status update failed: {str(e)}"}
        )
    
@router.get("/devices")
async def get_all_devices(
    db: Session = Depends(get_db),
    status: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all registered devices
    Optional parameters:
    - status: filter by status (working/removed)
    - skip: pagination offset
    - limit: max number of results
    """
    try:
        query = db.query(models.Device)
        
        # Apply status filter if provided
        if status in ["working", "removed"]:
            query = query.filter(models.Device.status == status)
        
        devices = query.offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "data": [
                {
                    "device_id": device.device_id,
                    "unique_code": device.unique_code,
                    "is_active": device.is_active,
                    "is_online": device.is_online,
                    "status": device.status
                }
                for device in devices
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"message": f"Failed to fetch devices: {str(e)}"}
        )
    
@router.get("/device-locations/{device_id}", status_code=200)
async def get_device_locations(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get location history for a specific device
    """
    try:
        # Verify device exists
        device = db.query(models.Device).filter(
            models.Device.device_id == device_id
        ).first()

        if not device:
            raise HTTPException(
                status_code=404,
                detail={"message": "Device not found"}
            )

        # Get locations
        locations = db.query(models.Location).filter(
            models.Location.device_id == device_id
        ).order_by(models.Location.timestamp.desc()).all()

        return {
            "status": "success",
            "data": [
                {
                    "location_id": loc.location_id,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "timestamp": loc.timestamp.isoformat()
                }
                for loc in locations
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"message": f"Failed to fetch locations: {str(e)}"}
        )


@router.post("/pair-device", status_code=200)
async def pair_device_with_pet(
    pair_data: dict,
    db: Session = Depends(get_db)
):
    """
    Pair an existing device with a pet
    Expects: {"unique_code": "string", "pet_id": int, "user_id": int}
    """
    try:
        # Validate input
        if not all(key in pair_data for key in ["unique_code", "pet_id", "user_id"]):
            raise HTTPException(
                status_code=422,
                detail={"message": "unique_code, pet_id, and user_id are required"}
            )

        unique_code = pair_data["unique_code"]
        pet_id = pair_data["pet_id"]
        user_id = pair_data["user_id"]

        # Check if device exists in xxdevice_db table
        device = db.query(models.Device).filter(
            models.Device.unique_code == unique_code
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail={"message": "Device with this unique code does not exist"}
            )
        
        # Check if device status is not 'removed'
        if device.status == "removed":
            raise HTTPException(
                status_code=400,
                detail={"message": "Device is not available for pairing"}
            )
        
        # Check if device is already paired with another pet
        if device.pet_id is not None and device.pet_id != pet_id:
            raise HTTPException(
                status_code=400,
                detail={"message": "Device is already paired with another pet"}
            )
        
        # Verify that the pet exists and belongs to the user
        pet = db.query(models.Pet).filter(
            models.Pet.id == pet_id,
            models.Pet.user_id == user_id
        ).first()
        
        if not pet:
            raise HTTPException(
                status_code=404,
                detail={"message": "Pet not found or does not belong to this user"}
            )
        
        # Update device with pet_id, user_id, and set is_active to True
        device.pet_id = pet_id
        device.user_id = user_id
        device.is_active = True
        device.paired_at = datetime.utcnow()
        
        db.commit()
        db.refresh(device)
        
        return {
            "status": "success",
            "message": f"Device successfully paired with {pet.name}",
            "data": {
                "device_id": device.device_id,
                "unique_code": device.unique_code,
                "pet_id": device.pet_id,
                "user_id": device.user_id,
                "is_active": device.is_active,
                "paired_at": device.paired_at.isoformat() if device.paired_at else None
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": f"Pairing failed: {str(e)}"}
        )

@router.patch("/update-pair-device", status_code=200)
async def update_pair_device_with_pet(
    pair_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update device pairing with a pet
    Expects: {"unique_code": "string", "pet_id": int, "user_id": int}
    """
    try:
        # Validate input
        if not all(key in pair_data for key in ["unique_code", "pet_id", "user_id"]):
            raise HTTPException(
                status_code=422,
                detail={"message": "unique_code, pet_id, and user_id are required"}
            )

        unique_code = pair_data["unique_code"]
        pet_id = pair_data["pet_id"]
        user_id = pair_data["user_id"]

        # Find the current device paired with this pet
        current_device = db.query(models.Device).filter(
            models.Device.pet_id == pet_id
        ).first()

        # Check if new device exists
        new_device = db.query(models.Device).filter(
            models.Device.unique_code == unique_code
        ).first()
        
        if not new_device:
            raise HTTPException(
                status_code=404,
                detail={"message": "Device with this unique code does not exist"}
            )
        
        # Check if new device status is not 'removed'
        if new_device.status == "removed":
            raise HTTPException(
                status_code=400,
                detail={"message": "Device is not available for pairing"}
            )
        
        # Check if new device is already paired with another pet
        if new_device.pet_id is not None and new_device.pet_id != pet_id:
            raise HTTPException(
                status_code=400,
                detail={"message": "Device is already paired with another pet"}
            )
        
        # Verify that the pet exists and belongs to the user
        pet = db.query(models.Pet).filter(
            models.Pet.id == pet_id,
            models.Pet.user_id == user_id
        ).first()
        
        if not pet:
            raise HTTPException(
                status_code=404,
                detail={"message": "Pet not found or does not belong to this user"}
            )
        
        # If there's a current device, unpair it
        if current_device and current_device.device_id != new_device.device_id:
            current_device.pet_id = None
            current_device.user_id = None
            current_device.is_active = False
            current_device.paired_at = None
        
        # Update new device with pet_id, user_id, and set is_active to True
        new_device.pet_id = pet_id
        new_device.user_id = user_id
        new_device.is_active = True
        new_device.paired_at = datetime.utcnow()
        
        db.commit()
        db.refresh(new_device)
        
        return {
            "status": "success",
            "message": f"Device successfully updated for {pet.name}",
            "data": {
                "device_id": new_device.device_id,
                "unique_code": new_device.unique_code,
                "pet_id": new_device.pet_id,
                "user_id": new_device.user_id,
                "is_active": new_device.is_active,
                "paired_at": new_device.paired_at.isoformat() if new_device.paired_at else None
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": f"Update pairing failed: {str(e)}"}
        )

@router.get("/{pet_id}/device-info", status_code=200)
async def get_pet_device_info(
    pet_id: int,
    db: Session = Depends(get_db)
):
    """
    Get device information for a specific pet
    """
    try:
        # Find device paired with this pet
        device = db.query(models.Device).filter(
            models.Device.pet_id == pet_id
        ).first()
        
        if not device:
            return {
                "status": "success",
                "data": None,
                "message": "No device paired with this pet"
            }
        
        return {
            "status": "success",
            "data": {
                "device_id": device.device_id,
                "unique_code": device.unique_code,
                "is_active": device.is_active,
                "is_online": device.is_online,
                "status": device.status,
                "paired_at": device.paired_at.isoformat() if device.paired_at else None
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to fetch device info: {str(e)}"}
        )
# @router.get("/{pet_id}/device-info", status_code=200)
# async def get_pet_device_info(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get device information for a specific pet
#     """
#     try:
#         # Find device paired with this pet
#         device = db.query(models.Device).filter(
#             models.Device.pet_id == pet_id
#         ).first()
        
#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "No device paired with this pet"}
#             )
        
#         return {
#             "status": "success",
#             "data": {
#                 "device_id": device.device_id,
#                 "unique_code": device.unique_code,
#                 "is_active": device.is_active,
#                 "is_online": device.is_online,
#                 "status": device.status,
#                 "paired_at": device.paired_at.isoformat() if device.paired_at else None
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Failed to fetch device info: {str(e)}"}
#         )

@router.get("/{pet_id}/current-location", status_code=200)
async def get_pet_current_location(
    pet_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current location of a pet using its paired device
    """
    try:
        # Find device paired with this pet
        device = db.query(models.Device).filter(
            models.Device.pet_id == pet_id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail={"message": "No device paired with this pet"}
            )
        
        # Get the most recent location from xxlocation_db
        latest_location = db.query(models.Location).filter(
            models.Location.device_id == device.device_id
        ).order_by(models.Location.timestamp.desc()).first()
        
        if not latest_location:
            raise HTTPException(
                status_code=404,
                detail={"message": "No location data available for this pet"}
            )
        
        return {
            "status": "success",
            "data": {
                "location_id": latest_location.location_id,
                "latitude": latest_location.latitude,
                "longitude": latest_location.longitude,
                "timestamp": latest_location.timestamp.isoformat(),
                "device_id": device.device_id,
                "unique_code": device.unique_code
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to fetch current location: {str(e)}"}
        )



@router.patch("/{pet_id}/device-activation", status_code=200)
async def toggle_device_activation(
    pet_id: int,
    activation_data: dict,
    db: Session = Depends(get_db)
):
    """
    Manually toggle device activation for Safe at Home pets
    Expects: {"is_active": true/false}
    """
    try:
        # Validate input
        if "is_active" not in activation_data or not isinstance(activation_data["is_active"], bool):
            raise HTTPException(
                status_code=422,
                detail={"message": "is_active boolean value is required"}
            )

        is_active = activation_data["is_active"]

        # Find the pet
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        
        if not pet:
            raise HTTPException(
                status_code=404,
                detail={"message": "Pet not found"}
            )

        # Check if pet status allows manual device control
        if pet.status not in ["Safe at Home"]:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Device activation can only be controlled for 'Safe at Home' pets. Current status: {pet.status}"}
            )

        # Find paired device
        device = db.query(models.Device).filter(
            models.Device.pet_id == pet_id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail={"message": "No device paired with this pet"}
            )
        
        # Update device activation
        old_status = device.is_active
        device.is_active = is_active
        
        db.commit()
        db.refresh(device)
        
        return {
            "status": "success",
            "message": f"Device {'activated' if is_active else 'deactivated'} successfully",
            "data": {
                "pet_id": pet.id,
                "pet_name": pet.name,
                "pet_status": pet.status,
                "device_id": device.device_id,
                "unique_code": device.unique_code,
                "old_active_status": old_status,
                "new_active_status": device.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": f"Device activation toggle failed: {str(e)}"}
        )






















@router.post("/verify-pet-image")
async def verify_pet_image_endpoint(file: UploadFile = File(...)):
    try:
        # Verify the file is actually an image first
        if not file.content_type.startswith('image/'):
            return {
                "is_valid": False,
                "message": "File is not a valid image",
                "error": "invalid_file_type"
            }

        # Read the first few bytes to verify it's an image
        header = await file.read(10)
        await file.seek(0)
        if not header.startswith((b'\xff\xd8', b'\x89PNG\r\n\x1a\n')):  # JPEG/PNG magic numbers
            return {
                "is_valid": False,
                "message": "Invalid image file format",
                "error": "invalid_image_format"
            }

        # Now try the pet verification
        verification = await verify_pet_image(file)
        await file.seek(0)  # Reset for potential reuse
        
        return verification

    except Exception as e:
        await file.seek(0)
        return {
            "is_valid": False,
            "message": "Could not process image",
            "error": "processing_error",
            "details": str(e)
        }


@router.post("/upload-image")
async def upload_pet_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # ✅ Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only images are allowed")

        # ✅ Get latest pet
        latest_pet = db.query(models.Pet).order_by(models.Pet.id.desc()).first()
        if not latest_pet:
            raise HTTPException(status_code=404, detail="No pet found")

        pet_id = latest_pet.id
        filename = "main.jpg"  # ✅ Fixed name
        path_in_bucket = f"{pet_id}/{filename}"  # e.g., 1/main.jpg

        # ✅ Read file contents
        content = await file.read()

        # ✅ Upload to Supabase
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=path_in_bucket,
            file=content,
            file_options={"content-type": file.content_type, "x-upsert": "true"}
        )

        # ✅ Handle errors
        if res.get("error"):
            raise HTTPException(status_code=500, detail=res["error"]["message"])

        # ✅ Update DB record with the full path
        latest_pet.image = path_in_bucket  # This will be "1/main.jpg"
        db.commit()

        # ✅ Public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path_in_bucket}"

        return {
            "filename": filename,
            "file_path": path_in_bucket,  # Returns "1/main.jpg"
            "url": public_url
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/dashboard")
async def get_pets(user_id: int, db: Session = Depends(get_db)):
    try:
        pets = db.query(models.Pet).filter(models.Pet.user_id == user_id).all()
        
        if not pets:
            return {"pets": []}  # Return empty array instead of error
        
        return {
            "pets": [
                {
                    "id": pet.id,
                    "name": pet.name,
                    "type": pet.type,
                    "gender": pet.gender,
                    "description": pet.description,
                    "date": pet.date.isoformat(),  # Convert datetime to string
                    "address": pet.address,
                    "status": pet.status,
                    "image": pet.image,  # This will now be "1/main.jpg" format
                }
                for pet in pets
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pets: {str(e)}")
    






@router.get("/{pet_id}")
async def get_pet(pet_id: int, db: Session = Depends(get_db)):
    try:
        pet = db.query(models.Pet).outerjoin(models.PetHealth).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Generate Supabase URL for main image
        image_url = None
        if pet.image:
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{pet.image}"
        
        # Generate URLs for additional images
        additional_image_urls = []
        if pet.additional_images:
            for img in pet.additional_images:
                additional_image_urls.append(f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{img}")
        
        response = {
            "id": pet.id,
            "name": pet.name,
            "type": pet.type,
            "gender": pet.gender,
            "description": pet.description,
            "date": pet.date.isoformat() if pet.date else None,
            "address": pet.address,
            "status": pet.status,
            "image": pet.image,  # Keep filename for backend (now "1/main.jpg")
            "image_url": image_url,  # Add URL for frontend
            "additional_images": pet.additional_images or [],
            "additional_image_urls": additional_image_urls,  # Add URLs for frontend
            "is_published": pet.is_published,
            "admin_approved": pet.admin_approved,
            "health_info": None
        }
        
        # Add health info if exists (keep existing code)
        if pet.health_info:
            response["health_info"] = {
                "vaccinated": pet.health_info.vaccinated,
                "spayed_neutered": pet.health_info.spayed_neutered,
                "health_details": pet.health_info.health_details,
                "good_with": {
                    "children": pet.health_info.good_with_children,
                    "dogs": pet.health_info.good_with_dogs,
                    "cats": pet.health_info.good_with_cats,
                    "elderly": pet.health_info.good_with_elderly,
                    "strangers": pet.health_info.good_with_strangers
                },
                "energy_level": pet.health_info.energy_level,
                "temperament_personality": pet.health_info.temperament_personality,
                "reason_for_adoption": pet.health_info.reason_for_adoption
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Add to backend/app/routers/pet_router.py
@router.delete("/{pet_id}")
async def delete_pet(
    pet_id: int,
    user_id: int = None,  # Will be passed from frontend
    db: Session = Depends(get_db)
):
    try:
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Verify ownership using user_id
        if pet.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this pet")
        
        # Delete images from Supabase if they exist
        try:
            if pet.image:
                supabase.storage.from_(SUPABASE_BUCKET).remove([pet.image])
            
            if pet.additional_images:
                supabase.storage.from_(SUPABASE_BUCKET).remove(pet.additional_images)
        except Exception as e:
            print(f"Warning: Failed to delete images from Supabase: {str(e)}")
        
        db.delete(pet)
        db.commit()
        
        return {"message": "Pet deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete pet: {str(e)}")

@router.patch("/{pet_id}/status")
async def update_pet_status(
    pet_id: int,
    status_data: dict,
    db: Session = Depends(get_db)
):
    try:
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        new_status = status_data.get("status")
        
        # Validate status transition
        valid_transitions = {
            "Safe at Home": ["Lost"],
            "Lost": ["Safe at Home", "Pet I Found"],
            "Pet I Found": ["Reunited"],
            "Reunited": ["Lost"]
        }
        
        if pet.status in valid_transitions and new_status not in valid_transitions[pet.status]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change status from {pet.status} to {new_status}"
            )
        
        # Automatically unpublish when status changes to certain values
        if new_status in ["Safe at Home", "Reunited"]:
            pet.is_published = False
        
        pet.status = new_status
        db.commit()
        db.refresh(pet)
        
        return {
            "message": f"Status updated to {new_status}",
            "status": pet.status,
            "is_published": pet.is_published
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{pet_id}/publish")
async def toggle_publish_status(
    pet_id: int,
    publish_data: dict,
    db: Session = Depends(get_db)
):
    try:
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        new_publish_status = publish_data.get("publish", False)
        pet.is_published = new_publish_status
        
        # Reset admin approval when unpublishing
        if not new_publish_status:
            pet.admin_approved = False
        
        db.commit()
        db.refresh(pet)
        
        action = "published" if new_publish_status else "unpublished"
        return {
            "message": f"Pet {action} successfully",
            "is_published": pet.is_published,
            "admin_approved": pet.admin_approved  # Include this in response
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # Add admin approval endpoint
@router.patch("/{pet_id}/admin-approval")
async def update_admin_approval(
    pet_id: int,
    approval_data: dict,
    db: Session = Depends(get_db),
    # Add admin auth check here in production
):
    try:
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        pet.admin_approved = approval_data.get("approved", False)
        db.commit()
        db.refresh(pet)
        
        return {
            "message": "Admin approval status updated",
            "admin_approved": pet.admin_approved
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    



@router.patch("/{pet_id}")
async def update_pet_details(
    pet_id: int,
    pet_data: dict,
    db: Session = Depends(get_db)
):
    try:
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Update basic pet fields
        updatable_fields = ['name', 'type', 'gender', 'description', 'address', 'date', 'status']
        for field in updatable_fields:
            if field in pet_data:
                setattr(pet, field, pet_data[field])
        
        # Update or create health info
        if 'health_info' in pet_data:
            health_data = pet_data['health_info']
            
            if pet.health_info:
                # Update existing health record
                health_info = pet.health_info
                
                # Update all health fields
                health_fields = [
                    'vaccinated', 'spayed_neutered', 'health_details',
                    'energy_level', 'temperament_personality', 'reason_for_adoption',
                    'good_with_children', 'good_with_dogs', 'good_with_cats',
                    'good_with_elderly', 'good_with_strangers'
                ]
                
                for field in health_fields:
                    if field in health_data:
                        setattr(health_info, field, health_data[field])
                
                # Handle good_with object if sent as a group
                if 'good_with' in health_data:
                    good_with = health_data['good_with']
                    health_info.good_with_children = good_with.get('children', health_info.good_with_children)
                    health_info.good_with_dogs = good_with.get('dogs', health_info.good_with_dogs)
                    health_info.good_with_cats = good_with.get('cats', health_info.good_with_cats)
                    health_info.good_with_elderly = good_with.get('elderly', health_info.good_with_elderly)
                    health_info.good_with_strangers = good_with.get('strangers', health_info.good_with_strangers)
            else:
                # Create new health record
                health_info = models.PetHealth(
                    pet_id=pet.id,
                    vaccinated=health_data.get('vaccinated'),
                    spayed_neutered=health_data.get('spayed_neutered'),
                    health_details=health_data.get('health_details'),
                    good_with_children=health_data.get('good_with', {}).get('children', False),
                    good_with_dogs=health_data.get('good_with', {}).get('dogs', False),
                    good_with_cats=health_data.get('good_with', {}).get('cats', False),
                    good_with_elderly=health_data.get('good_with', {}).get('elderly', False),
                    good_with_strangers=health_data.get('good_with', {}).get('strangers', False),
                    energy_level=health_data.get('energy_level'),
                    temperament_personality=health_data.get('temperament_personality'),
                    reason_for_adoption=health_data.get('reason_for_adoption')
                )
                db.add(health_info)
        
        db.commit()
        db.refresh(pet)
        
        return {
            "message": "Pet details updated successfully",
            "pet_id": pet.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

# @router.post("/{pet_id}/update-image")
# async def update_pet_image_endpoint(
#     pet_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Validate file
#         if not file.content_type.startswith('image/'):
#             raise HTTPException(400, detail="Only images allowed")

#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Generate filename with proper path structure
#         filename = "main.jpg"
#         path_in_bucket = f"{pet_id}/{filename}"  # This creates "1/main.jpg"
#         content = await file.read()

#         # Delete old image if exists
#         if pet.image:
#             try:
#                 supabase.storage.from_(SUPABASE_BUCKET).remove([pet.image])
#             except:
#                 pass  # Continue even if deletion fails

#         # Upload new image to Supabase
#         res = supabase.storage.from_(SUPABASE_BUCKET).upload(
#             path=path_in_bucket,
#             file=content,
#             file_options={"content-type": file.content_type, "x-upsert": "true"}
#         )

#         # Handle errors
#         if res.get("error"):
#             raise HTTPException(status_code=500, detail=res["error"]["message"])

#         # Update pet record with the full path
#         pet.image = path_in_bucket  # This will be "1/main.jpg"
#         db.commit()

#         public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path_in_bucket}"

#         return {
#             "success": True,
#             "filename": filename,
#             "file_path": path_in_bucket,  # Returns "1/main.jpg"
#             "url": public_url
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/{pet_id}/update-image")
async def update_pet_image_endpoint(
    pet_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, detail="Only images allowed")

        # Verify pet exists
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")

        # Generate filename with proper path structure
        filename = "main.jpg"
        path_in_bucket = f"{pet_id}/{filename}"  # This creates "1/main.jpg"
        content = await file.read()

        # Delete old image if exists
        if pet.image:
            try:
                supabase.storage.from_(SUPABASE_BUCKET).remove([pet.image])
            except:
                pass  # Continue even if deletion fails

        # Upload new image to Supabase
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=path_in_bucket,
                file=content,
                file_options={"content-type": file.content_type, "x-upsert": "true"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        # Update pet record with the full path
        pet.image = path_in_bucket  # This will be "1/main.jpg"
        db.commit()

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path_in_bucket}"

        return {
            "success": True,
            "filename": filename,
            "file_path": path_in_bucket,  # Returns "1/main.jpg"
            "url": public_url
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))





# @router.post("/{pet_id}/add-additional-image")
# async def add_additional_image(
#     pet_id: int,
#     file: UploadFile = File(...),
#     image_type: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Validate image type
#         valid_types = ["face", "side", "fur"]
#         if image_type not in valid_types:
#             raise HTTPException(status_code=400, detail="Invalid image type. Must be face, side, or fur")

#         # Generate filename with proper path structure
#         filename = f"{image_type}.jpg"
#         path_in_bucket = f"{pet_id}/{filename}"  # This creates "1/face.jpg", "1/side.jpg", etc.
#         content = await file.read()

#         # Initialize additional_images if None
#         if pet.additional_images is None:
#             pet.additional_images = []

#         # Check if this image type already exists and remove old one
#         old_path = None
#         for i, img_path in enumerate(pet.additional_images):
#             if img_path.endswith(f"/{filename}"):
#                 old_path = pet.additional_images.pop(i)
#                 break

#         # Delete old image from Supabase if exists
#         if old_path:
#             try:
#                 supabase.storage.from_(SUPABASE_BUCKET).remove([old_path])
#             except:
#                 pass

#         # Upload new image to Supabase
#         res = supabase.storage.from_(SUPABASE_BUCKET).upload(
#             path=path_in_bucket,
#             file=content,
#             file_options={"content-type": file.content_type, "x-upsert": "true"}
#         )

#         # Handle errors
#         if res.get("error"):
#             raise HTTPException(status_code=500, detail=res["error"]["message"])

#         # Update the pet's additional_images array with the full path
#         pet.additional_images.append(path_in_bucket)  # This will be "1/face.jpg"
#         flag_modified(pet, "additional_images")
#         db.commit()
#         db.refresh(pet)

#         public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path_in_bucket}"

#         return {
#             "success": True,
#             "filename": filename,
#             "file_path": path_in_bucket,  # Returns "1/face.jpg"
#             "url": public_url,
#             "all_images": pet.additional_images
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/{pet_id}/add-additional-image")
async def add_additional_image(
    pet_id: int,
    file: UploadFile = File(...),
    image_type: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Verify pet exists
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")

        # Validate image type
        valid_types = ["face", "side", "fur"]
        if image_type not in valid_types:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be face, side, or fur")

        # Generate filename with proper path structure
        filename = f"{image_type}.jpg"
        path_in_bucket = f"{pet_id}/{filename}"  # This creates "1/face.jpg", "1/side.jpg", etc.
        content = await file.read()

        # Initialize additional_images if None
        if pet.additional_images is None:
            pet.additional_images = []

        # Check if this image type already exists and remove old one
        old_filename = None
        for i, img_filename in enumerate(pet.additional_images):
            if img_filename == filename:  # Check if filename already exists
                old_filename = pet.additional_images.pop(i)
                break

        # Delete old image from Supabase if exists
        if old_filename:
            old_path_in_bucket = f"{pet_id}/{old_filename}"
            try:
                supabase.storage.from_(SUPABASE_BUCKET).remove([old_path_in_bucket])
            except:
                pass

        # Upload new image to Supabase
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=path_in_bucket,
                file=content,
                file_options={"content-type": file.content_type, "x-upsert": "true"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        # Update the pet's additional_images array with the filename only
        # This will store ["face.jpg", "side.jpg", "fur.jpg"] in the database
        pet.additional_images.append(filename)  # This will be "face.jpg", "side.jpg", etc.
        flag_modified(pet, "additional_images")
        db.commit()
        db.refresh(pet)

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path_in_bucket}"

        return {
            "success": True,
            "filename": filename,
            "file_path": path_in_bucket,  # Returns "1/face.jpg"
            "url": public_url,
            "all_images": pet.additional_images
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pet_id}/remove-additional-image")
async def remove_additional_image(
    pet_id: int,
    index: int = Query(..., description="Index of image to remove"),
    db: Session = Depends(get_db)
):
    try:
        # Verify pet exists
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")

        if not pet.additional_images or index >= len(pet.additional_images):
            raise HTTPException(status_code=400, detail="Invalid image index")

        # Get the path to remove
        image_path = pet.additional_images[index]

        # Delete from Supabase
        try:
            supabase.storage.from_(SUPABASE_BUCKET).remove([image_path])
        except Exception as e:
            print(f"Warning: Failed to delete from Supabase: {str(e)}")

        # Remove from the array
        pet.additional_images.pop(index)
        flag_modified(pet, "additional_images")
        db.commit()

        return {
            "success": True,
            "message": "Image removed successfully",
            "remaining_images": pet.additional_images
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{pet_id}/clear-additional-images")
# async def clear_additional_images(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Delete additional images from Supabase
#         if pet.additional_images:
#             try:
#                 supabase.storage.from_(SUPABASE_BUCKET).remove(pet.additional_images)
#             except Exception as e:
#                 print(f"Warning: Failed to delete images from Supabase: {str(e)}")

#         # Clear additional_images array in database but keep main image
#         if pet.additional_images:
#             pet.additional_images = []
#             flag_modified(pet, "additional_images")
#             db.commit()

#         return {
#             "success": True,
#             "message": "Additional images cleared successfully",
#             "main_image": pet.image  # Return the preserved main image path
#         }

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pet_id}/clear-additional-images")
async def clear_additional_images(
    pet_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Verify pet exists
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")

        # Delete additional images from Supabase
        if pet.additional_images:
            try:
                # Convert filenames to full paths for Supabase deletion
                paths_to_delete = [f"{pet_id}/{filename}" for filename in pet.additional_images]
                supabase.storage.from_(SUPABASE_BUCKET).remove(paths_to_delete)
            except Exception as e:
                print(f"Warning: Failed to delete images from Supabase: {str(e)}")

        # Clear additional_images array in database but keep main image
        if pet.additional_images:
            pet.additional_images = []
            flag_modified(pet, "additional_images")
            db.commit()

        return {
            "success": True,
            "message": "Additional images cleared successfully",
            "main_image": pet.image  # Return the preserved main image path
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/{pet_id}/generate-fingerprint")
async def generate_pet_fingerprint(
    pet_id: int,
    status_data: dict = Body(...),  # Accept status in request body
    db: Session = Depends(get_db)
):
    # Validate pet exists
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    # Validate pet type
    if pet.type.lower() not in ['dog', 'cat']:
        raise HTTPException(status_code=400, detail="Pet type must be either 'dog' or 'cat'")
    
    # Validate status
    status = status_data.get('status', '').lower()
    if status not in ['lost', 'pet i found']:
        raise HTTPException(
            status_code=400, 
            detail="Status must be either 'lost' or 'found'"
        )
    
    # Generate fingerprint with type and status metadata
    result = feature_extractor.generate_fingerprint(
        pet_id=pet_id,
        pet_type=pet.type.lower(),
        status=status
    )
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Missing required images (main.jpg, face.jpg, side.jpg, fur.jpg)"
        )
    
    # Update pet record
    pet.has_generated_fingerprint = True
    db.commit()
    
    return {
        "message": "Fingerprint generated successfully",
        "pet_id": pet_id,
        "status": status
    }
    
@router.get("/{pet_id}/check-fingerprint")
async def check_fingerprint_exists(
    pet_id: int,
    db: Session = Depends(get_db)
):
    features_path = Path(f"app/uploads/pet_images/{pet_id}/features.json")
    return {"exists": features_path.exists()}







@router.get("/{pet_id}/flyer-data")
def get_pet_flyer_data(pet_id: int, db: Session = Depends(get_db)):
    try:
        # Get pet data
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        owner = db.query(models.User).filter(models.User.id == pet.user_id).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        # Handle image path - pet.image is now already in "1/main.jpg" format
        image_path = pet.image if pet.image else None
        
        return {
            "success": True,
            "data": {
                "pet": {
                    "id": pet.id,
                    "name": pet.name,
                    "type": pet.type,
                    "breed": pet.breed if hasattr(pet, 'breed') else "Unknown",
                    "color": pet.color if hasattr(pet, 'color') else "Unknown",
                    "description": pet.description,
                    "date_lost": pet.date.strftime("%Y-%m-%d") if pet.date else "Unknown",
                    "last_seen": pet.address,
                    "image": image_path,  # Now returns "1/main.jpg" directly
                    "image_url": f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{image_path}" if image_path else None
                },
                "owner": {
                    "name": getattr(owner, 'full_name', getattr(owner, 'name', 'Unknown')),
                    "phone": getattr(owner, 'phone', getattr(owner, 'phone_number', 'Unknown')),
                    "email": owner.email
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/{pet_id}/find-similar")
async def find_similar_pets(
    pet_id: int,
    threshold: float = Query(0.65, ge=0.5, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    max_distance: str = Query("no limit", description="Distance filter: 5m, 1km, 3km, 5km, no limit"),
    db: Session = Depends(get_db)
):
    try:
        # Get source pet and its features (existing code remains unchanged)
        source_pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not source_pet:
            raise HTTPException(status_code=404, detail="Source pet not found")
            
        source_path = Path(f"app/uploads/pet_images/{pet_id}/features.json")
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source pet fingerprint not found")
        
        with open(source_path) as f:
            source_data = json.load(f)
        
        source_type = source_data['metadata']['type']
        source_status = source_pet.status.lower()

        if source_status == "lost":
            target_status = "pet i found"
        elif source_status == "pet i found":
            target_status = "lost"
        else:
            return {
                "matches": [],
                "search_criteria": {
                    "source_status": source_status,
                    "message": "Similarity search only works between 'Lost' and 'Pet I Found' statuses"
                }
            }
        
        source_coords = (source_pet.latitude, source_pet.longitude) if source_pet.latitude and source_pet.longitude else None
        
        distance_map = {
            "5m": 0.005,
            "1km": 1,
            "3km": 3,
            "5km": 5,
            "no limit": float('inf')
        }
        max_km = distance_map.get(max_distance.lower(), float('inf'))
        
        matches = []
        pets_dir = Path("app/uploads/pet_images")
        
        for pet_dir in pets_dir.iterdir():
            if pet_dir.is_dir() and pet_dir.name != str(pet_id):
                features_path = pet_dir / "features.json"
                if features_path.exists():
                    target_pet = db.query(Pet).filter(Pet.id == int(pet_dir.name)).first()
                    if not target_pet or target_pet.user_id == source_pet.user_id:
                        continue
                        
                    if target_pet.status.lower() != target_status:
                        continue
                        
                    with open(features_path) as f:
                        target_data = json.load(f)
                    
                    if target_data['metadata']['type'] != source_type:
                        continue
                        
                    distance_km = None
                    if source_coords and target_pet.latitude and target_pet.longitude:
                        target_coords = (target_pet.latitude, target_pet.longitude)
                        distance_km = geodesic(source_coords, target_coords).km
                        if distance_km > max_km:
                            continue
                    
                    similarity = feature_extractor.compare_features(
                        source_data['features'],
                        target_data['features'],
                        source_type
                    )
                    if similarity >= threshold:
                        user = db.query(models.User).filter(models.User.id == target_pet.user_id).first()
                        
                        # Generate image URL for the match
                        image_url = None
                        if target_pet.image:
                            image_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{target_pet.image}"
                        
                        matches.append({
                            "pet_id": target_pet.id,
                            "name": target_pet.name,
                            "score": float(similarity),
                            "image_url": image_url,  # Now uses Supabase URL
                            "distance_km": float(distance_km) if distance_km else None,
                            "description": target_pet.description,
                            "date": target_pet.date.isoformat() if target_pet.date else None,
                            "status": target_pet.status,
                            "gender": target_pet.gender,
                            "address": target_pet.address,
                            "user": {
                                "id": user.id,
                                "name": user.name,
                                "profile_picture": user.profile_picture
                            } if user else None
                        })
        
        matches.sort(key=lambda x: x["score"], reverse=True)
        final_matches = matches[:limit]

        # Fixed Notification Logic (4-5 arguments only)
        for match in final_matches:
            if match["score"] >= 0.8:
                # Notify source pet owner
                if not db.query(models.UserNotification).filter(
                    models.UserNotification.user_id == source_pet.user_id,
                    models.UserNotification.related_url == f"/pets/{match['pet_id']}",
                    models.UserNotification.notification_type == "pet"
                ).first():
                    notification_message = f"Found {match['name']} ({(match['score']*100):.1f}% match)"
                    if match['distance_km']:
                        notification_message += f" {match['distance_km']:.1f}km away"
                    
                    db.add(models.UserNotification(
                        user_id=source_pet.user_id,
                        title=f"Potential {target_status} match",
                        message=notification_message,
                        notification_type="pet",
                        related_url=f"/pets/{match['pet_id']}",
                        created_at=datetime.utcnow()
                    ))

                # Notify matching pet owner
                if match["user"] and not db.query(models.UserNotification).filter(
                    models.UserNotification.user_id == match["user"]["id"],
                    models.UserNotification.related_url == f"/pets/{pet_id}",
                    models.UserNotification.notification_type == "pet"
                ).first():
                    notification_message = f"Your pet matches {source_pet.name} ({(match['score']*100):.1f}% match)"
                    if match['distance_km']:
                        notification_message += f" {match['distance_km']:.1f}km away"
                    
                    db.add(models.UserNotification(
                        user_id=match["user"]["id"],
                        title=f"Potential {source_status} match",
                        message=notification_message,
                        notification_type="pet",
                        related_url=f"/pets/{pet_id}",
                        created_at=datetime.utcnow()
                    ))

        # Existing search logging code remains unchanged
        existing_search = db.query(PetSimilaritySearch).filter(
            PetSimilaritySearch.source_pet_id == pet_id
        ).first()
        
        if existing_search:
            existing_search.search_timestamp = datetime.utcnow()
            existing_search.threshold = threshold
            existing_search.max_distance = max_distance
            existing_search.matches_found = len(final_matches)
            existing_search.highest_similarity_score = final_matches[0]["score"] if final_matches else None
            existing_search.was_successful = len(final_matches) > 0
            existing_search.total_searches = existing_search.total_searches + 1
        else:
            search_record = PetSimilaritySearch(
                source_pet_id=pet_id,
                threshold=threshold,
                max_distance=max_distance,
                matches_found=len(final_matches),
                highest_similarity_score=final_matches[0]["score"] if final_matches else None,
                was_successful=len(final_matches) > 0,
                total_searches=1
            )
            db.add(search_record)
        
        db.commit()
        
        return {
            "matches": final_matches,
            "search_criteria": {
                "source_status": source_status,
                "target_status": target_status,
                "threshold": threshold,
                "message": f"Showing {target_status} pets that match your {source_status} pet" if final_matches else f"No matching {target_status} pets found"
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

 


# @router.get("/rehome/")
# async def get_rehome_pets(
#     type: Optional[str] = None,
#     gender: Optional[str] = None,
#     location: Optional[str] = None,
#     good_with: Optional[str] = None,
#     energy_level: Optional[str] = None,
#     user_id: Optional[int] = None,
#     skip: int = 0,
#     limit: int = 100,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Base query with joins
#         query = db.query(
#             models.Pet,
#             models.User.name.label("owner_name"),
#             models.User.phone_number.label("owner_phone"),
#             models.PetHealth  # Include PetHealth directly in the query
#         )\
#             .join(models.User, models.Pet.user_id == models.User.id)\
#             .outerjoin(models.PetHealth, models.Pet.id == models.PetHealth.pet_id)\
#             .filter(models.Pet.status == "Rehome Pet")\
#             .filter(models.Pet.is_published == True)\
#             .filter(models.Pet.admin_approved == True)
        
#         # Exclude user's own pets if user_id is provided
#         if user_id:
#             query = query.filter(models.Pet.user_id != user_id)
        
#         # Apply filters
#         if type:
#             query = query.filter(models.Pet.type.ilike(f"%{type}%"))
#         if gender:
#             query = query.filter(models.Pet.gender.ilike(f"%{gender}%"))
#         if location:
#             query = query.filter(models.Pet.address.ilike(f"%{location}%"))
        
#         # New filters for PetHealth fields
#         if good_with:
#             for trait in good_with.split(','):
#                 trait = trait.strip().lower()
#                 if trait == "children":
#                     query = query.filter(models.PetHealth.good_with_children == True)
#                 elif trait == "dogs":
#                     query = query.filter(models.PetHealth.good_with_dogs == True)
#                 elif trait == "cats":
#                     query = query.filter(models.PetHealth.good_with_cats == True)
#                 elif trait == "elderly":
#                     query = query.filter(models.PetHealth.good_with_elderly == True)
#                 elif trait == "strangers":
#                     query = query.filter(models.PetHealth.good_with_strangers == True)
        
#         if energy_level:
#             query = query.filter(models.PetHealth.energy_level.ilike(f"%{energy_level}%"))
        
#         # Execute query
#         results = query.offset(skip).limit(limit).all()
            
#         return [{
#             "id": pet.id,
#             "name": pet.name,
#             "type": pet.type,
#             "gender": pet.gender,
#             "image": pet.image,  # This is now "1/main.jpg" format
#             "location": pet.address,
#             "status": pet.status,
#             "additional_images": pet.additional_images,
#             "description": pet.description,
#             "date": pet.date.isoformat() if pet.date else None,
#             "latitude": pet.latitude,
#             "longitude": pet.longitude,
#             "user_id": pet.user_id,
#             "owner_info": {
#                 "name": owner_name,
#                 "phone": owner_phone
#             },
#             "health_info": {
#                 "vaccinated": health.vaccinated if health else None,
#                 "spayed_neutered": health.spayed_neutered if health else None,
#                 "good_with": {
#                     "children": health.good_with_children if health else None,
#                     "dogs": health.good_with_dogs if health else None,
#                     "cats": health.good_with_cats if health else None,
#                     "elderly": health.good_with_elderly if health else None,
#                     "strangers": health.good_with_strangers if health else None
#                 } if health else None,
#                 "energy_level": health.energy_level if health else None,
#                 "temperament_personality": health.temperament_personality if health else None,
#                 "reason_for_adoption": health.reason_for_adoption if health else None
#             }
#         } for pet, owner_name, owner_phone, health in results]  # Now includes health in unpacking

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/rehome/")
async def get_rehome_pets(
    type: Optional[str] = None,
    gender: Optional[str] = None,
    location: Optional[str] = None,
    good_with: Optional[str] = None,
    energy_level: Optional[str] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        # Base query with joins
        query = db.query(
            models.Pet,
            models.User.name.label("owner_name"),
            models.User.phone_number.label("owner_phone"),
            models.PetHealth  # Include PetHealth directly in the query
        )\
            .join(models.User, models.Pet.user_id == models.User.id)\
            .outerjoin(models.PetHealth, models.Pet.id == models.PetHealth.pet_id)\
            .filter(models.Pet.status == "Rehome Pet")\
            .filter(models.Pet.is_published == True)\
            .filter(models.Pet.admin_approved == True)
        
        # Exclude user's own pets if user_id is provided
        if user_id:
            query = query.filter(models.Pet.user_id != user_id)
        
        # Apply filters
        if type:
            query = query.filter(models.Pet.type.ilike(f"%{type}%"))
        if gender:
            query = query.filter(models.Pet.gender.ilike(f"%{gender}%"))
        if location:
            query = query.filter(models.Pet.address.ilike(f"%{location}%"))
        
        # New filters for PetHealth fields
        if good_with:
            for trait in good_with.split(','):
                trait = trait.strip().lower()
                if trait == "children":
                    query = query.filter(models.PetHealth.good_with_children == True)
                elif trait == "dogs":
                    query = query.filter(models.PetHealth.good_with_dogs == True)
                elif trait == "cats":
                    query = query.filter(models.PetHealth.good_with_cats == True)
                elif trait == "elderly":
                    query = query.filter(models.PetHealth.good_with_elderly == True)
                elif trait == "strangers":
                    query = query.filter(models.PetHealth.good_with_strangers == True)
        
        if energy_level:
            query = query.filter(models.PetHealth.energy_level.ilike(f"%{energy_level}%"))
        
        # Execute query
        results = query.offset(skip).limit(limit).all()
            
        return [{
            "id": pet.id,
            "name": pet.name,
            "type": pet.type,
            "gender": pet.gender,
            "image": pet.image,
            "location": pet.address,
            "status": pet.status,
            "additional_images": pet.additional_images,
            "description": pet.description,
            "date": pet.date.isoformat() if pet.date else None,
            "latitude": pet.latitude,
            "longitude": pet.longitude,
            "user_id": pet.user_id,
            "owner_info": {
                "name": owner_name,
                "phone": owner_phone
            },
            "health_info": {
                "vaccinated": health.vaccinated if health else None,
                "spayed_neutered": health.spayed_neutered if health else None,
                "good_with": {
                    "children": health.good_with_children if health else None,
                    "dogs": health.good_with_dogs if health else None,
                    "cats": health.good_with_cats if health else None,
                    "elderly": health.good_with_elderly if health else None,
                    "strangers": health.good_with_strangers if health else None
                } if health else None,
                "energy_level": health.energy_level if health else None,
                "temperament_personality": health.temperament_personality if health else None,
                "reason_for_adoption": health.reason_for_adoption if health else None
            }
        } for pet, owner_name, owner_phone, health in results]  # Now includes health in unpacking

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adoption-application")
async def submit_adoption_application(
    form_data: dict,
    db: Session = Depends(get_db)
):
    try:
        # Validate required user_id
        if 'user_id' not in form_data:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Create new application
        application = models.AdoptionForm(
            user_id=form_data['user_id'],
            full_name=form_data.get('full_name'),
            contact_info=form_data.get('contact_info'),
            housing_type=form_data.get('housing_type'),
            landlord_allows_pets=form_data.get('landlord_allows_pets'),
            household_members=form_data.get('household_members'),
            pet_allergies=form_data.get('pet_allergies'),
            allergy_types=form_data.get('allergy_types'),
            primary_caregiver=form_data.get('primary_caregiver'),
            expense_responsibility=form_data.get('expense_responsibility'),
            daily_alone_time=form_data.get('daily_alone_time'),
            alone_time_plan=form_data.get('alone_time_plan'),
            emergency_care=form_data.get('emergency_care'),
            current_pets=form_data.get('current_pets'),
            past_pets=form_data.get('past_pets'),
            past_pets_outcome=form_data.get('past_pets_outcome'),
            adoption_reason=form_data.get('adoption_reason'),
            household_agreement=form_data.get('household_agreement'),
            household_disagreement_reason=form_data.get('household_disagreement_reason')
        )
        
        db.add(application)
        db.commit()
        
        return {
            "success": True,
            "message": "Application submitted successfully",
            "application_id": application.id,
            "status": application.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-adoption-applications/{user_id}")
async def get_user_applications(
    user_id: int,
    db: Session = Depends(get_db)
):
    try:
        applications = db.query(models.AdoptionForm)\
            .filter(models.AdoptionForm.user_id == user_id)\
            .order_by(models.AdoptionForm.created_at.desc())\
            .all()
            
        return {
            "success": True,
            "data": [
                {
                    "id": app.id,
                    "status": app.status,
                    "created_at": app.created_at.isoformat(),
                    "full_name": app.full_name,
                    "contact_info": app.contact_info
                } for app in applications
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# backend/app/routers/pet_router.py
@router.get("/pet/{pet_id}/adoption-status")
async def check_adoption_status(
    pet_id: int,
    user_id: int,  # Pass adopter's user_id as query parameter
    db: Session = Depends(get_db)
):
    try:
        # Check if user has approved application
        approved_application = db.query(models.AdoptionForm)\
            .filter(
                models.AdoptionForm.user_id == user_id,
                models.AdoptionForm.status == 'approved'
            )\
            .first()
        
        if not approved_application:
            return {"can_adopt": False, "reason": "No approved application"}
            
        return {"can_adopt": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pet/{pet_id}/adopt", status_code=status.HTTP_201_CREATED)
async def adopt_pet(
    pet_id: int,
    user_id: int,  # Adopter's user_id
    db: Session = Depends(get_db)
):
    """
    Submit or update an adoption request for a pet
    - Creates new adoption record if none exists
    - Updates existing record if request already pending
    - Notifies both owner and adopter
    """
    try:
        # Verify pet exists and get owner
        pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Check if pet is already adopted
        if pet.status.lower() == "adopted":
            raise HTTPException(
                status_code=400,
                detail="This pet has already been adopted"
            )

        # Check if adoption record already exists
        existing_adoption = db.query(models.AdoptedPet)\
            .filter(models.AdoptedPet.pet_id == pet_id)\
            .filter(models.AdoptedPet.adopter_id == user_id)\
            .first()
        
        if existing_adoption:
            # Update existing record
            existing_adoption.status = 'pending'
            existing_adoption.updated_at = datetime.utcnow()
            message = "Adoption request updated"
            adoption_id = existing_adoption.id
        else:
            # Create new adoption record
            adoption = models.AdoptedPet(
                pet_id=pet_id,
                owner_id=pet.user_id,
                adopter_id=user_id,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.add(adoption)
            db.flush()  # Get the ID before commit
            message = "Adoption request submitted"
            adoption_id = adoption.id

        # Notify pet owner
        create_notification(
            db,
            pet.user_id,
            "New Adoption Request",
            f"Someone wants to adopt {pet.name}",
            "pet"
        )

        # Notify adopter
        create_notification(
            db,
            user_id,
            "Adoption Request Sent",
            f"Your request to adopt {pet.name} has been submitted",
            "pet"
        )

        db.commit()
        
        return {
            "success": True,
            "message": message,
            "adoption_id": adoption_id,
            "pet_name": pet.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process adoption: {str(e)}"
        )

@router.get("/adoptions/")
async def get_user_adoptions(
    user_id: int = Query(..., description="ID of the user to fetch adoptions for"),
    role: str = Query(..., description="'owner' or 'adopter' to filter by role"),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.AdoptedPet)\
            .join(models.Pet, models.AdoptedPet.pet_id == models.Pet.id)\
            .join(models.User, models.AdoptedPet.owner_id == models.User.id)\
            .outerjoin(models.AdoptionForm, models.AdoptionForm.user_id == models.AdoptedPet.adopter_id)
        
        if role == "owner":
            query = query.filter(models.AdoptedPet.owner_id == user_id)
        elif role == "adopter":
            query = query.filter(models.AdoptedPet.adopter_id == user_id)
        
        if status:
            query = query.filter(models.AdoptedPet.status == status)
        
        adoptions = query.order_by(models.AdoptedPet.created_at.desc()).all()
        
        result = []
        for adoption in adoptions:
            # Get adoption form (if exists)
            adoption_form = None
            if adoption.adopter and adoption.adopter.adoption_forms:
                adoption_form = adoption.adopter.adoption_forms[0]
            
            adoption_data = {
                "id": adoption.id,
                "pet_id": adoption.pet_id,
                "pet_name": adoption.pet.name,
                "pet_image": adoption.pet.image,  # This is now "1/main.jpg" format
                "pet_type": adoption.pet.type,
                "owner_id": adoption.owner_id,
                "owner_name": adoption.owner.name,
                "adopter_id": adoption.adopter_id,
                "adopter_name": db.query(models.User).filter(models.User.id == adoption.adopter_id).first().name,
                "status": adoption.status,
                "created_at": adoption.created_at.isoformat(),
                "updated_at": adoption.updated_at.isoformat() if adoption.updated_at else None,
                "adoption_form": {
                    "id": adoption_form.id if adoption_form else None,
                    "status": adoption_form.status if adoption_form else None,
                    "created_at": adoption_form.created_at.isoformat() if adoption_form and adoption_form.created_at else None,
                    
                    # Applicant Information
                    "full_name": adoption_form.full_name if adoption_form else None,
                    "contact_info": adoption_form.contact_info if adoption_form else None,
                    "housing_type": adoption_form.housing_type if adoption_form else None,
                    "landlord_allows_pets": adoption_form.landlord_allows_pets if adoption_form else None,
                    
                    # Household Details
                    "household_members": adoption_form.household_members if adoption_form else None,
                    "pet_allergies": adoption_form.pet_allergies if adoption_form else None,
                    "allergy_types": adoption_form.allergy_types if adoption_form else None,
                    
                    # Pet Care Plan
                    "primary_caregiver": adoption_form.primary_caregiver if adoption_form else None,
                    "expense_responsibility": adoption_form.expense_responsibility if adoption_form else None,
                    "daily_alone_time": adoption_form.daily_alone_time if adoption_form else None,
                    "alone_time_plan": adoption_form.alone_time_plan if adoption_form else None,
                    "emergency_care": adoption_form.emergency_care if adoption_form else None,
                    
                    # Pet Experience
                    "current_pets": adoption_form.current_pets if adoption_form else None,
                    "past_pets": adoption_form.past_pets if adoption_form else None,
                    "past_pets_outcome": adoption_form.past_pets_outcome if adoption_form else None,
                    
                    # Adoption Readiness
                    "adoption_reason": adoption_form.adoption_reason if adoption_form else None,
                    "household_agreement": adoption_form.household_agreement if adoption_form else None,
                    "household_disagreement_reason": adoption_form.household_disagreement_reason if adoption_form else None
                } if adoption_form else None
            }
            result.append(adoption_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/adoptions/{adoption_id}/status")
async def update_adoption_status(
    adoption_id: int,
    status_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update adoption status (owner only)
    Allowed statuses: pending, approved, rejected, completed
    """
    try:
        status = status_data.get("status", "").lower()
        valid_statuses = ["pending", "approved", "rejected", "cancelled", "completed"]
        
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        adoption = db.query(models.AdoptedPet)\
            .filter(models.AdoptedPet.id == adoption_id)\
            .first()
            
        if not adoption:
            raise HTTPException(status_code=404, detail="Adoption record not found")

        # Get related pet
        pet = db.query(models.Pet).filter(models.Pet.id == adoption.pet_id).first()
        
        # Update status
        previous_status = adoption.status
        adoption.status = status
        adoption.updated_at = datetime.utcnow()

        # Update pet status if adoption is approved
        if status == "Approved" and pet:
            pet.status = "Adopted"
            pet.updated_at = datetime.utcnow()

        db.commit()

        # Notify both parties
        status_message = {
            "approved": "approved your adoption request for",
            "rejected": "rejected your adoption request for",
            "completed": "completed the adoption process for"
        }.get(status, f"changed status to {status} for")

        if status in status_message and pet:
            # Notify adopter
            create_notification(
                db,
                adoption.adopter_id,
                f"Adoption {status.capitalize()}",
                f"The owner has {status_message} {pet.name}",
                "pet"
            )

            # Notify owner
            create_notification(
                db,
                adoption.owner_id,
                f"Adoption {status.capitalize()}",
                f"You've {status_message} {pet.name}",
                "pet"
            )

        return {
            "success": True,
            "message": f"Adoption status updated to {status}",
            "adoption_id": adoption.id,
            "pet_name": pet.name if pet else None,
            "previous_status": previous_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update adoption status: {str(e)}"
        )























































# # # backend/app/routers/pet_router.py
# # backend/app/routers/pet_router.py
# from fastapi import APIRouter, HTTPException, Depends, status, Body, UploadFile, Query, File, Form
# from sqlalchemy.orm import Session
# from app.database.database import get_db
# from app.models import models
# from fastapi.responses import JSONResponse
# from geopy.distance import geodesic  # Install with: pip install geopy
# from app.models.models import User
# from typing import Dict, Optional
# from app.models.models import PetSimilaritySearch
# from datetime import datetime
# from fastapi.staticfiles import StaticFiles
# from ..services.pet_detector import verify_pet_image
# from fastapi.staticfiles import StaticFiles
# from sqlalchemy.orm.attributes import flag_modified
# from ..models.models import Pet
# from sqlalchemy import func

# import os
# import re
# import uuid
# from pathlib import Path
# from PIL import Image
# import io
# import json

# # === TensorFlow conditional import ===
# try:
#     import tensorflow as tf
#     from ..services.pet_feature_extractor import PetFeatureExtractor
#     USE_TENSORFLOW = True
#     feature_extractor = PetFeatureExtractor()
# except ImportError:
#     print("TensorFlow not available. Feature extraction is disabled.")
#     USE_TENSORFLOW = False
#     feature_extractor = None

# # === Upload directory setup ===
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist

# router = APIRouter(prefix="/api/pets", tags=["pets"])
# router.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")

# # If you have old string path usage, keep for compatibility
# UPLOAD_DIR = "app/uploads/pet_images"
# os.makedirs(UPLOAD_DIR, exist_ok=True)



# # Add ONLY if needed ↓
# def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str = "system"):
#     """Helper function to create notifications"""
#     notification = models.UserNotification(
#         user_id=user_id,
#         title=title,
#         message=message,
#         notification_type=notification_type,
#         is_read=False,
#         created_at=datetime.utcnow()
#     )
#     db.add(notification)
#     db.commit()
#     db.refresh(notification)
#     return notification

# @router.post("/")
# async def create_pet(pet_data: dict, db: Session = Depends(get_db)):
#     try:
#         pet_date = datetime.strptime(pet_data["date"], "%Y-%m-%dT%H:%M")
        
#         db_pet = models.Pet(
#             name=pet_data["name"],
#             type=pet_data.get("type", "Dog"),
#             gender=pet_data.get("gender", "Male"),
#             description=pet_data.get("description", ""),
#             date=pet_date,
#             address=pet_data.get("address", ""),
#             status=pet_data.get("status", "Safe at Home"),
#             image=pet_data.get("image"),
#             user_id=pet_data["user_id"],
#             latitude=pet_data.get("latitude"),
#             longitude=pet_data.get("longitude")
#         )
        
#         db.add(db_pet)
#         db.commit()
#         db.refresh(db_pet)

#         # Optional: Notify the pet owner ↓
#         create_notification(
#             db,
#             pet_data["user_id"],
#             "New Pet Added",
#             f"{pet_data['name']} was registered successfully",
#             "pet"
#         )
        
#         return {"message": "Pet saved successfully", "pet_id": db_pet.id}
    
#     except ValueError as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=f"Failed to create pet: {str(e)}")




# @router.post("/register-device", status_code=201)
# async def register_device(device_data: dict, db: Session = Depends(get_db)):
#     """
#     Register a new pet tracking device
#     Expects: {"unique_code": "string"}
#     """
#     try:
#         # Validate input
#         if not device_data.get("unique_code"):
#             raise HTTPException(
#                 status_code=422,
#                 detail={"message": "unique_code is required"}
#             )

#         unique_code = device_data["unique_code"]  # Extract the string value

#         # Check for existing device - including status check
#         existing = db.query(models.Device).filter(
#             models.Device.unique_code == unique_code,
#             models.Device.status != "removed"  # Only consider non-removed devices
#         ).first()
        
#         if existing:
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "Device already registered"}
#             )
        
#         # Create new device with status
#         db_device = models.Device(
#             unique_code=unique_code,
#             is_active=False,
#             is_online=False,
#             status="working"  # Explicitly set status (default would work too)
#         )
        
#         db.add(db_device)
#         db.commit()
#         db.refresh(db_device)
        
#         return {
#             "status": "success",
#             "message": "Device registered",
#             "data": {
#                 "device_id": db_device.device_id,
#                 "unique_code": db_device.unique_code,
#                 "status": db_device.status  # Include status in response
#             }
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=400,
#             detail={"message": f"Registration failed: {str(e)}"}
#         )
    

# @router.patch("/update-device-status/{device_id}", status_code=200)
# async def update_device_status(
#     device_id: int,
#     status_data: dict,
#     db: Session = Depends(get_db)
# ):
#     """
#     Update device status
#     Expects: {"status": "working" | "removed"}
#     """
#     try:
#         if not status_data.get("status") or status_data["status"] not in ["working", "removed"]:
#             raise HTTPException(
#                 status_code=422,
#                 detail={"message": "Valid status (working/removed) is required"}
#             )

#         device = db.query(models.Device).filter(
#             models.Device.device_id == device_id
#         ).first()

#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Device not found"}
#             )

#         device.status = status_data["status"]
#         db.commit()
        
#         return {
#             "status": "success",
#             "message": "Device status updated",
#             "data": {
#                 "device_id": device.device_id,
#                 "new_status": device.status
#             }
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=400,
#             detail={"message": f"Status update failed: {str(e)}"}
#         )
    
# @router.get("/devices")
# async def get_all_devices(
#     db: Session = Depends(get_db),
#     status: str = None,
#     skip: int = 0,
#     limit: int = 100
# ):
#     """
#     Get all registered devices
#     Optional parameters:
#     - status: filter by status (working/removed)
#     - skip: pagination offset
#     - limit: max number of results
#     """
#     try:
#         query = db.query(models.Device)
        
#         # Apply status filter if provided
#         if status in ["working", "removed"]:
#             query = query.filter(models.Device.status == status)
        
#         devices = query.offset(skip).limit(limit).all()
        
#         return {
#             "status": "success",
#             "data": [
#                 {
#                     "device_id": device.device_id,
#                     "unique_code": device.unique_code,
#                     "is_active": device.is_active,
#                     "is_online": device.is_online,
#                     "status": device.status
#                 }
#                 for device in devices
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=400,
#             detail={"message": f"Failed to fetch devices: {str(e)}"}
#         )
    
# @router.get("/device-locations/{device_id}", status_code=200)
# async def get_device_locations(
#     device_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get location history for a specific device
#     """
#     try:
#         # Verify device exists
#         device = db.query(models.Device).filter(
#             models.Device.device_id == device_id
#         ).first()

#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Device not found"}
#             )

#         # Get locations
#         locations = db.query(models.Location).filter(
#             models.Location.device_id == device_id
#         ).order_by(models.Location.timestamp.desc()).all()

#         return {
#             "status": "success",
#             "data": [
#                 {
#                     "location_id": loc.location_id,
#                     "latitude": loc.latitude,
#                     "longitude": loc.longitude,
#                     "timestamp": loc.timestamp.isoformat()
#                 }
#                 for loc in locations
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=400,
#             detail={"message": f"Failed to fetch locations: {str(e)}"}
#         )


# @router.post("/pair-device", status_code=200)
# async def pair_device_with_pet(
#     pair_data: dict,
#     db: Session = Depends(get_db)
# ):
#     """
#     Pair an existing device with a pet
#     Expects: {"unique_code": "string", "pet_id": int, "user_id": int}
#     """
#     try:
#         # Validate input
#         if not all(key in pair_data for key in ["unique_code", "pet_id", "user_id"]):
#             raise HTTPException(
#                 status_code=422,
#                 detail={"message": "unique_code, pet_id, and user_id are required"}
#             )

#         unique_code = pair_data["unique_code"]
#         pet_id = pair_data["pet_id"]
#         user_id = pair_data["user_id"]

#         # Check if device exists in xxdevice_db table
#         device = db.query(models.Device).filter(
#             models.Device.unique_code == unique_code
#         ).first()
        
#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Device with this unique code does not exist"}
#             )
        
#         # Check if device status is not 'removed'
#         if device.status == "removed":
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "Device is not available for pairing"}
#             )
        
#         # Check if device is already paired with another pet
#         if device.pet_id is not None and device.pet_id != pet_id:
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "Device is already paired with another pet"}
#             )
        
#         # Verify that the pet exists and belongs to the user
#         pet = db.query(models.Pet).filter(
#             models.Pet.id == pet_id,
#             models.Pet.user_id == user_id
#         ).first()
        
#         if not pet:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Pet not found or does not belong to this user"}
#             )
        
#         # Update device with pet_id, user_id, and set is_active to True
#         device.pet_id = pet_id
#         device.user_id = user_id
#         device.is_active = True
#         device.paired_at = datetime.utcnow()
        
#         db.commit()
#         db.refresh(device)
        
#         return {
#             "status": "success",
#             "message": f"Device successfully paired with {pet.name}",
#             "data": {
#                 "device_id": device.device_id,
#                 "unique_code": device.unique_code,
#                 "pet_id": device.pet_id,
#                 "user_id": device.user_id,
#                 "is_active": device.is_active,
#                 "paired_at": device.paired_at.isoformat() if device.paired_at else None
#             }
#         }
        
#     except HTTPException:
#         # Re-raise HTTP exceptions as-is
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Pairing failed: {str(e)}"}
#         )

# @router.patch("/update-pair-device", status_code=200)
# async def update_pair_device_with_pet(
#     pair_data: dict,
#     db: Session = Depends(get_db)
# ):
#     """
#     Update device pairing with a pet
#     Expects: {"unique_code": "string", "pet_id": int, "user_id": int}
#     """
#     try:
#         # Validate input
#         if not all(key in pair_data for key in ["unique_code", "pet_id", "user_id"]):
#             raise HTTPException(
#                 status_code=422,
#                 detail={"message": "unique_code, pet_id, and user_id are required"}
#             )

#         unique_code = pair_data["unique_code"]
#         pet_id = pair_data["pet_id"]
#         user_id = pair_data["user_id"]

#         # Find the current device paired with this pet
#         current_device = db.query(models.Device).filter(
#             models.Device.pet_id == pet_id
#         ).first()

#         # Check if new device exists
#         new_device = db.query(models.Device).filter(
#             models.Device.unique_code == unique_code
#         ).first()
        
#         if not new_device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Device with this unique code does not exist"}
#             )
        
#         # Check if new device status is not 'removed'
#         if new_device.status == "removed":
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "Device is not available for pairing"}
#             )
        
#         # Check if new device is already paired with another pet
#         if new_device.pet_id is not None and new_device.pet_id != pet_id:
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "Device is already paired with another pet"}
#             )
        
#         # Verify that the pet exists and belongs to the user
#         pet = db.query(models.Pet).filter(
#             models.Pet.id == pet_id,
#             models.Pet.user_id == user_id
#         ).first()
        
#         if not pet:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Pet not found or does not belong to this user"}
#             )
        
#         # If there's a current device, unpair it
#         if current_device and current_device.device_id != new_device.device_id:
#             current_device.pet_id = None
#             current_device.user_id = None
#             current_device.is_active = False
#             current_device.paired_at = None
        
#         # Update new device with pet_id, user_id, and set is_active to True
#         new_device.pet_id = pet_id
#         new_device.user_id = user_id
#         new_device.is_active = True
#         new_device.paired_at = datetime.utcnow()
        
#         db.commit()
#         db.refresh(new_device)
        
#         return {
#             "status": "success",
#             "message": f"Device successfully updated for {pet.name}",
#             "data": {
#                 "device_id": new_device.device_id,
#                 "unique_code": new_device.unique_code,
#                 "pet_id": new_device.pet_id,
#                 "user_id": new_device.user_id,
#                 "is_active": new_device.is_active,
#                 "paired_at": new_device.paired_at.isoformat() if new_device.paired_at else None
#             }
#         }
        
#     except HTTPException:
#         # Re-raise HTTP exceptions as-is
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Update pairing failed: {str(e)}"}
#         )

# @router.get("/{pet_id}/device-info", status_code=200)
# async def get_pet_device_info(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get device information for a specific pet
#     """
#     try:
#         # Find device paired with this pet
#         device = db.query(models.Device).filter(
#             models.Device.pet_id == pet_id
#         ).first()
        
#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "No device paired with this pet"}
#             )
        
#         return {
#             "status": "success",
#             "data": {
#                 "device_id": device.device_id,
#                 "unique_code": device.unique_code,
#                 "is_active": device.is_active,
#                 "is_online": device.is_online,
#                 "status": device.status,
#                 "paired_at": device.paired_at.isoformat() if device.paired_at else None
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Failed to fetch device info: {str(e)}"}
#         )

# @router.get("/{pet_id}/current-location", status_code=200)
# async def get_pet_current_location(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get current location of a pet using its paired device
#     """
#     try:
#         # Find device paired with this pet
#         device = db.query(models.Device).filter(
#             models.Device.pet_id == pet_id
#         ).first()
        
#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "No device paired with this pet"}
#             )
        
#         # Get the most recent location from xxlocation_db
#         latest_location = db.query(models.Location).filter(
#             models.Location.device_id == device.device_id
#         ).order_by(models.Location.timestamp.desc()).first()
        
#         if not latest_location:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "No location data available for this pet"}
#             )
        
#         return {
#             "status": "success",
#             "data": {
#                 "location_id": latest_location.location_id,
#                 "latitude": latest_location.latitude,
#                 "longitude": latest_location.longitude,
#                 "timestamp": latest_location.timestamp.isoformat(),
#                 "device_id": device.device_id,
#                 "unique_code": device.unique_code
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Failed to fetch current location: {str(e)}"}
#         )



# @router.patch("/{pet_id}/device-activation", status_code=200)
# async def toggle_device_activation(
#     pet_id: int,
#     activation_data: dict,
#     db: Session = Depends(get_db)
# ):
#     """
#     Manually toggle device activation for Safe at Home pets
#     Expects: {"is_active": true/false}
#     """
#     try:
#         # Validate input
#         if "is_active" not in activation_data or not isinstance(activation_data["is_active"], bool):
#             raise HTTPException(
#                 status_code=422,
#                 detail={"message": "is_active boolean value is required"}
#             )

#         is_active = activation_data["is_active"]

#         # Find the pet
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        
#         if not pet:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "Pet not found"}
#             )

#         # Check if pet status allows manual device control
#         if pet.status not in ["Safe at Home"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": f"Device activation can only be controlled for 'Safe at Home' pets. Current status: {pet.status}"}
#             )

#         # Find paired device
#         device = db.query(models.Device).filter(
#             models.Device.pet_id == pet_id
#         ).first()
        
#         if not device:
#             raise HTTPException(
#                 status_code=404,
#                 detail={"message": "No device paired with this pet"}
#             )
        
#         # Update device activation
#         old_status = device.is_active
#         device.is_active = is_active
        
#         db.commit()
#         db.refresh(device)
        
#         return {
#             "status": "success",
#             "message": f"Device {'activated' if is_active else 'deactivated'} successfully",
#             "data": {
#                 "pet_id": pet.id,
#                 "pet_name": pet.name,
#                 "pet_status": pet.status,
#                 "device_id": device.device_id,
#                 "unique_code": device.unique_code,
#                 "old_active_status": old_status,
#                 "new_active_status": device.is_active
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail={"message": f"Device activation toggle failed: {str(e)}"}
#         )





# @router.post("/verify-pet-image")
# async def verify_pet_image_endpoint(file: UploadFile = File(...)):
#     try:
#         # Verify the file is actually an image first
#         if not file.content_type.startswith('image/'):
#             return {
#                 "is_valid": False,
#                 "message": "File is not a valid image",
#                 "error": "invalid_file_type"
#             }

#         # Read the first few bytes to verify it's an image
#         header = await file.read(10)
#         await file.seek(0)
#         if not header.startswith((b'\xff\xd8', b'\x89PNG\r\n\x1a\n')):  # JPEG/PNG magic numbers
#             return {
#                 "is_valid": False,
#                 "message": "Invalid image file format",
#                 "error": "invalid_image_format"
#             }

#         # Now try the pet verification
#         verification = await verify_pet_image(file)
#         await file.seek(0)  # Reset for potential reuse
        
#         return verification

#     except Exception as e:
#         await file.seek(0)
#         return {
#             "is_valid": False,
#             "message": "Could not process image",
#             "error": "processing_error",
#             "details": str(e)
#         }


# @router.post("/upload-image")
# async def upload_pet_image(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         if not file.filename:
#             raise HTTPException(status_code=400, detail="No file provided")

#         # Get the latest pet (if exists)
#         latest_pet = db.query(models.Pet).order_by(models.Pet.id.desc()).first()
        
#         # Create upload directory
#         upload_dir = Path("app/uploads/pet_images")
#         upload_dir.mkdir(exist_ok=True, parents=True)

#         # Case 1: No pet exists yet (first-time upload)
#         if not latest_pet:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
#             file_path = upload_dir / filename
            
#             with file_path.open("wb") as buffer:
#                 content = await file.read()
#                 buffer.write(content)

#             return {
#                 "filename": filename,
#                 "file_path": f"/uploads/pet_images/{filename}"
#             }

#         # Case 2: Pet exists (subsequent uploads)
#         else:
#             pet_id = latest_pet.id
#             pet_dir = upload_dir / str(pet_id)
#             pet_dir.mkdir(exist_ok=True)
            
#             filename = "main.jpg"
#             file_path = pet_dir / filename
            
#             with file_path.open("wb") as buffer:
#                 content = await file.read()
#                 buffer.write(content)

#             # Update the pet's image path
#             latest_pet.image = f"{pet_id}/{filename}"
#             db.commit()

#             return {
#                 "filename": f"{pet_id}/{filename}",
#                 "file_path": f"/uploads/pet_images/{pet_id}/{filename}"
#             }

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))




# @router.get("/dashboard")
# async def get_pets(user_id: int, db: Session = Depends(get_db)):
#     try:
#         pets = db.query(models.Pet).filter(models.Pet.user_id == user_id).all()
        
#         if not pets:
#             return {"pets": []}  # Return empty array instead of error
        
#         return {
#             "pets": [
#                 {
#                     "id": pet.id,
#                     "name": pet.name,
#                     "type": pet.type,
#                     "gender": pet.gender,
#                     "description": pet.description,
#                     "date": pet.date.isoformat(),  # Convert datetime to string
#                     "address": pet.address,
#                     "status": pet.status,
#                     "image": pet.image,
#                 }
#                 for pet in pets
#             ]
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch pets: {str(e)}")
    





# @router.get("/{pet_id}")
# async def get_pet(pet_id: int, db: Session = Depends(get_db)):
#     try:
#         # Get pet with health info using a join
#         pet = db.query(models.Pet).outerjoin(models.PetHealth).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         # Base pet data
#         response = {
#             "id": pet.id,
#             "name": pet.name,
#             "type": pet.type,
#             "gender": pet.gender,
#             "description": pet.description,
#             "date": pet.date.isoformat() if pet.date else None,
#             "address": pet.address,
#             "status": pet.status,
#             "image": pet.image,
#             "additional_images": pet.additional_images or [],
#             "is_published": pet.is_published,
#             "admin_approved": pet.admin_approved,
#             "health_info": None
#         }
        
#         # Add health info if exists
#         if pet.health_info:
#             response["health_info"] = {
#                 "vaccinated": pet.health_info.vaccinated,
#                 "spayed_neutered": pet.health_info.spayed_neutered,
#                 "health_details": pet.health_info.health_details,
#                 "good_with": {
#                     "children": pet.health_info.good_with_children,
#                     "dogs": pet.health_info.good_with_dogs,
#                     "cats": pet.health_info.good_with_cats,
#                     "elderly": pet.health_info.good_with_elderly,
#                     "strangers": pet.health_info.good_with_strangers
#                 },
#                 "energy_level": pet.health_info.energy_level,
#                 "temperament_personality": pet.health_info.temperament_personality,
#                 "reason_for_adoption": pet.health_info.reason_for_adoption
#             }
        
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# # Add to backend/app/routers/pet_router.py
# @router.delete("/{pet_id}")
# async def delete_pet(
#     pet_id: int,
#     user_id: int = None,  # Will be passed from frontend
#     db: Session = Depends(get_db)
# ):
#     try:
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         # Verify ownership using user_id
#         if pet.user_id != user_id:
#             raise HTTPException(status_code=403, detail="Not authorized to delete this pet")
        
#         # First delete the associated image file if it exists
#         if pet.image:
#             try:
#                 image_path = os.path.join(UPLOAD_DIR, pet.image)
#                 if os.path.exists(image_path):
#                     os.remove(image_path)
#             except Exception as e:
#                 print(f"Warning: Failed to delete image file: {str(e)}")
        
#         db.delete(pet)
#         db.commit()
        
#         return {"message": "Pet deleted successfully"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=f"Failed to delete pet: {str(e)}")

# @router.patch("/{pet_id}/status")
# async def update_pet_status(
#     pet_id: int,
#     status_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         new_status = status_data.get("status")
        
#         # Validate status transition
#         valid_transitions = {
#             "Safe at Home": ["Lost"],
#             "Lost": ["Safe at Home", "Pet I Found"],
#             "Pet I Found": ["Reunited"],
#             "Reunited": ["Lost"]
#         }
        
#         if pet.status in valid_transitions and new_status not in valid_transitions[pet.status]:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Cannot change status from {pet.status} to {new_status}"
#             )
        
#         # Automatically unpublish when status changes to certain values
#         if new_status in ["Safe at Home", "Reunited"]:
#             pet.is_published = False
        
#         pet.status = new_status
#         db.commit()
#         db.refresh(pet)
        
#         return {
#             "message": f"Status updated to {new_status}",
#             "status": pet.status,
#             "is_published": pet.is_published
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))

# @router.patch("/{pet_id}/publish")
# async def toggle_publish_status(
#     pet_id: int,
#     publish_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         new_publish_status = publish_data.get("publish", False)
#         pet.is_published = new_publish_status
        
#         # Reset admin approval when unpublishing
#         if not new_publish_status:
#             pet.admin_approved = False
        
#         db.commit()
#         db.refresh(pet)
        
#         action = "published" if new_publish_status else "unpublished"
#         return {
#             "message": f"Pet {action} successfully",
#             "is_published": pet.is_published,
#             "admin_approved": pet.admin_approved  # Include this in response
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))

#     # Add admin approval endpoint
# @router.patch("/{pet_id}/admin-approval")
# async def update_admin_approval(
#     pet_id: int,
#     approval_data: dict,
#     db: Session = Depends(get_db),
#     # Add admin auth check here in production
# ):
#     try:
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         pet.admin_approved = approval_data.get("approved", False)
#         db.commit()
#         db.refresh(pet)
        
#         return {
#             "message": "Admin approval status updated",
#             "admin_approved": pet.admin_approved
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
    


# @router.patch("/{pet_id}")
# async def update_pet_details(
#     pet_id: int,
#     pet_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         # Update basic pet fields
#         updatable_fields = ['name', 'type', 'gender', 'description', 'address', 'date', 'status']
#         for field in updatable_fields:
#             if field in pet_data:
#                 setattr(pet, field, pet_data[field])
        
#         # Update or create health info
#         if 'health_info' in pet_data:
#             health_data = pet_data['health_info']
            
#             if pet.health_info:
#                 # Update existing health record
#                 health_info = pet.health_info
                
#                 # Update all health fields
#                 health_fields = [
#                     'vaccinated', 'spayed_neutered', 'health_details',
#                     'energy_level', 'temperament_personality', 'reason_for_adoption',
#                     'good_with_children', 'good_with_dogs', 'good_with_cats',
#                     'good_with_elderly', 'good_with_strangers'
#                 ]
                
#                 for field in health_fields:
#                     if field in health_data:
#                         setattr(health_info, field, health_data[field])
                
#                 # Handle good_with object if sent as a group
#                 if 'good_with' in health_data:
#                     good_with = health_data['good_with']
#                     health_info.good_with_children = good_with.get('children', health_info.good_with_children)
#                     health_info.good_with_dogs = good_with.get('dogs', health_info.good_with_dogs)
#                     health_info.good_with_cats = good_with.get('cats', health_info.good_with_cats)
#                     health_info.good_with_elderly = good_with.get('elderly', health_info.good_with_elderly)
#                     health_info.good_with_strangers = good_with.get('strangers', health_info.good_with_strangers)
#             else:
#                 # Create new health record
#                 health_info = models.PetHealth(
#                     pet_id=pet.id,
#                     vaccinated=health_data.get('vaccinated'),
#                     spayed_neutered=health_data.get('spayed_neutered'),
#                     health_details=health_data.get('health_details'),
#                     good_with_children=health_data.get('good_with', {}).get('children', False),
#                     good_with_dogs=health_data.get('good_with', {}).get('dogs', False),
#                     good_with_cats=health_data.get('good_with', {}).get('cats', False),
#                     good_with_elderly=health_data.get('good_with', {}).get('elderly', False),
#                     good_with_strangers=health_data.get('good_with', {}).get('strangers', False),
#                     energy_level=health_data.get('energy_level'),
#                     temperament_personality=health_data.get('temperament_personality'),
#                     reason_for_adoption=health_data.get('reason_for_adoption')
#                 )
#                 db.add(health_info)
        
#         db.commit()
#         db.refresh(pet)
        
#         return {
#             "message": "Pet details updated successfully",
#             "pet_id": pet.id
#         }
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
    

# @router.post("/{pet_id}/update-image")
# async def update_pet_image_endpoint(
#     pet_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify the file is actually an image first
#         if not file.content_type.startswith('image/'):
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "is_valid": False,
#                     "message": "File is not a valid image",
#                     "error": "invalid_file_type"
#                 }
#             )

#         # Read the first few bytes to verify it's an image
#         header = await file.read(10)
#         await file.seek(0)
#         if not header.startswith((b'\xff\xd8', b'\x89PNG\r\n\x1a\n')):  # JPEG/PNG magic numbers
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "is_valid": False,
#                     "message": "Invalid image file format",
#                     "error": "invalid_image_format"
#                 }
#             )

#         # Now try the pet verification
#         verification = await verify_pet_image(file)
#         await file.seek(0)  # Reset for potential reuse
        
#         if not verification.get('is_valid'):
#             raise HTTPException(
#                 status_code=400,
#                 detail=verification
#             )

#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Create pet-specific directory if it doesn't exist
#         pet_dir = Path(UPLOAD_DIR) / str(pet_id)
#         pet_dir.mkdir(exist_ok=True, parents=True)

#         # Generate filename and path
#         filename = "main.jpg"
#         file_path = pet_dir / filename

#         # Save the new image
#         with file_path.open("wb") as buffer:
#             while content := await file.read(1024 * 1024):  # 1MB chunks
#                 buffer.write(content)

#         # Update the pet's image path in database
#         relative_path = f"{pet_id}/{filename}"
#         pet.image = relative_path
#         db.commit()

#         return {
#             "success": True,
#             "filename": relative_path,
#             "file_path": f"/uploads/pet_images/{relative_path}",
#             "verification": verification
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "is_valid": False,
#                 "message": "Could not process image",
#                 "error": "processing_error",
#                 "details": str(e)
#             }
#         )



# @router.post("/{pet_id}/add-additional-image")
# async def add_additional_image(
#     pet_id: int,
#     file: UploadFile = File(...),
#     image_type: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Validate image type
#         valid_types = ["face", "side", "fur"]
#         if image_type not in valid_types:
#             raise HTTPException(status_code=400, detail="Invalid image type. Must be face, side, or fur")

#         # Create pet directory if it doesn't exist
#         pet_dir = Path(UPLOAD_DIR) / str(pet_id)
#         pet_dir.mkdir(exist_ok=True, parents=True)

#         # Generate filename
#         filename = f"{image_type}.jpg"
#         file_path = pet_dir / filename

#         # Initialize additional_images if None
#         if pet.additional_images is None:
#             pet.additional_images = []

#         # Check if this image type already exists
#         if filename in pet.additional_images:
#             raise HTTPException(status_code=400, detail=f"{image_type} view already exists")

#         # Save the image
#         with file_path.open("wb") as buffer:
#             while content := await file.read(1024 * 1024):  # 1MB chunks
#                 buffer.write(content)

#         # Update the pet's additional_images array
#         pet.additional_images.append(filename)
        
#         # Explicitly mark the field as modified
#         from sqlalchemy.orm.attributes import flag_modified
#         flag_modified(pet, "additional_images")
        
#         db.commit()
#         db.refresh(pet)

#         return {
#             "success": True,
#             "filename": filename,
#             "file_path": f"/uploads/pet_images/{pet_id}/{filename}",
#             "all_images": pet.additional_images
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{pet_id}/remove-additional-image")
# async def remove_additional_image(
#     pet_id: int,
#     index: int = Query(..., description="Index of image to remove"),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         if not pet.additional_images or index >= len(pet.additional_images):
#             raise HTTPException(status_code=400, detail="Invalid image index")

#         # Get the filename to remove
#         filename = pet.additional_images[index]
#         file_path = Path(UPLOAD_DIR) / str(pet_id) / filename

#         # Delete the file if it exists
#         if file_path.exists():
#             file_path.unlink()

#         # Remove from the array
#         pet.additional_images.pop(index)
#         db.commit()

#         return {
#             "success": True,
#             "message": "Image removed successfully",
#             "remaining_images": pet.additional_images
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{pet_id}/clear-additional-images")
# async def clear_additional_images(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Verify pet exists
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")

#         # Clear additional images from filesystem
#         pet_dir = Path(UPLOAD_DIR) / str(pet_id)
#         if pet_dir.exists():
#             # Only delete face.jpg, side.jpg, fur.jpg
#             for filename in ["face.jpg", "side.jpg", "fur.jpg"]:
#                 file_path = pet_dir / filename
#                 if file_path.exists():
#                     try:
#                         file_path.unlink()
#                     except Exception as e:
#                         print(f"Warning: Failed to delete {file_path}: {str(e)}")

#         # Clear additional_images array in database but keep main image
#         if pet.additional_images:
#             pet.additional_images = []
#             from sqlalchemy.orm.attributes import flag_modified
#             flag_modified(pet, "additional_images")
#             db.commit()

#         return {
#             "success": True,
#             "message": "Additional images cleared successfully",
#             "main_image": pet.image  # Return the preserved main image
#         }

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))
    

# @router.post("/{pet_id}/generate-fingerprint")
# async def generate_pet_fingerprint(
#     pet_id: int,
#     status_data: dict = Body(...),  # Accept status in request body
#     db: Session = Depends(get_db)
# ):
#     # Validate pet exists
#     pet = db.query(Pet).filter(Pet.id == pet_id).first()
#     if not pet:
#         raise HTTPException(status_code=404, detail="Pet not found")
    
#     # Validate pet type
#     if pet.type.lower() not in ['dog', 'cat']:
#         raise HTTPException(status_code=400, detail="Pet type must be either 'dog' or 'cat'")
    
#     # Validate status
#     status = status_data.get('status', '').lower()
#     if status not in ['lost', 'pet i found']:
#         raise HTTPException(
#             status_code=400, 
#             detail="Status must be either 'lost' or 'found'"
#         )
    
#     # Generate fingerprint with type and status metadata
#     result = feature_extractor.generate_fingerprint(
#         pet_id=pet_id,
#         pet_type=pet.type.lower(),
#         status=status
#     )
    
#     if not result:
#         raise HTTPException(
#             status_code=400,
#             detail="Missing required images (main.jpg, face.jpg, side.jpg, fur.jpg)"
#         )
    
#     # Update pet record
#     pet.has_generated_fingerprint = True
#     db.commit()
    
#     return {
#         "message": "Fingerprint generated successfully",
#         "pet_id": pet_id,
#         "status": status
#     }
    
# @router.get("/{pet_id}/check-fingerprint")
# async def check_fingerprint_exists(
#     pet_id: int,
#     db: Session = Depends(get_db)
# ):
#     features_path = Path(f"app/uploads/pet_images/{pet_id}/features.json")
#     return {"exists": features_path.exists()}





# @router.get("/{pet_id}/flyer-data")
# def get_pet_flyer_data(pet_id: int, db: Session = Depends(get_db)):
#     try:
#         # Get pet data
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         owner = db.query(models.User).filter(models.User.id == pet.user_id).first()
#         if not owner:
#             raise HTTPException(status_code=404, detail="Owner not found")
        
#         # Handle image path construction
#         image_path = None
#         if pet.image:
#             # Extract just the filename if full path is stored
#             image_name = pet.image.split('/')[-1] if '/' in pet.image else pet.image
#             image_path = f"{pet_id}/{image_name}"
        
#         return {
#             "success": True,
#             "data": {
#                 "pet": {
#                     "id": pet.id,  # Include pet ID in response
#                     "name": pet.name,
#                     "type": pet.type,
#                     "breed": pet.breed if hasattr(pet, 'breed') else "Unknown",
#                     "color": pet.color if hasattr(pet, 'color') else "Unknown",
#                     "description": pet.description,
#                     "date_lost": pet.date.strftime("%Y-%m-%d") if pet.date else "Unknown",
#                     "last_seen": pet.address,
#                     "image": image_path,  # Now returns "pet_id/filename.jpg"
#                     "image_url": f"/uploads/pet_images/{pet_id}/{pet.image.split('/')[-1]}" if pet.image else None
#                 },
#                 "owner": {
#                     "name": getattr(owner, 'full_name', getattr(owner, 'name', 'Unknown')),
#                     "phone": getattr(owner, 'phone', getattr(owner, 'phone_number', 'Unknown')),
#                     "email": owner.email
#                 }
#             }
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# @router.get("/{pet_id}/find-similar")
# async def find_similar_pets(
#     pet_id: int,
#     threshold: float = Query(0.65, ge=0.5, le=1.0),
#     limit: int = Query(10, ge=1, le=50),
#     max_distance: str = Query("no limit", description="Distance filter: 5m, 1km, 3km, 5km, no limit"),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Get source pet and its features (existing code remains unchanged)
#         source_pet = db.query(Pet).filter(Pet.id == pet_id).first()
#         if not source_pet:
#             raise HTTPException(status_code=404, detail="Source pet not found")
            
#         source_path = Path(f"app/uploads/pet_images/{pet_id}/features.json")
#         if not source_path.exists():
#             raise HTTPException(status_code=404, detail="Source pet fingerprint not found")
        
#         with open(source_path) as f:
#             source_data = json.load(f)
        
#         source_type = source_data['metadata']['type']
#         source_status = source_pet.status.lower()

#         if source_status == "lost":
#             target_status = "pet i found"
#         elif source_status == "pet i found":
#             target_status = "lost"
#         else:
#             return {
#                 "matches": [],
#                 "search_criteria": {
#                     "source_status": source_status,
#                     "message": "Similarity search only works between 'Lost' and 'Pet I Found' statuses"
#                 }
#             }
        
#         source_coords = (source_pet.latitude, source_pet.longitude) if source_pet.latitude and source_pet.longitude else None
        
#         distance_map = {
#             "5m": 0.005,
#             "1km": 1,
#             "3km": 3,
#             "5km": 5,
#             "no limit": float('inf')
#         }
#         max_km = distance_map.get(max_distance.lower(), float('inf'))
        
#         matches = []
#         pets_dir = Path("app/uploads/pet_images")
        
#         for pet_dir in pets_dir.iterdir():
#             if pet_dir.is_dir() and pet_dir.name != str(pet_id):
#                 features_path = pet_dir / "features.json"
#                 if features_path.exists():
#                     target_pet = db.query(Pet).filter(Pet.id == int(pet_dir.name)).first()
#                     if not target_pet or target_pet.user_id == source_pet.user_id:
#                         continue
                        
#                     if target_pet.status.lower() != target_status:
#                         continue
                        
#                     with open(features_path) as f:
#                         target_data = json.load(f)
                    
#                     if target_data['metadata']['type'] != source_type:
#                         continue
                        
#                     distance_km = None
#                     if source_coords and target_pet.latitude and target_pet.longitude:
#                         target_coords = (target_pet.latitude, target_pet.longitude)
#                         distance_km = geodesic(source_coords, target_coords).km
#                         if distance_km > max_km:
#                             continue
                    
#                     similarity = feature_extractor.compare_features(
#                         source_data['features'],
#                         target_data['features'],
#                         source_type
#                     )
#                     if similarity >= threshold:
#                         user = db.query(models.User).filter(models.User.id == target_pet.user_id).first()
#                         matches.append({
#                             "pet_id": target_pet.id,
#                             "name": target_pet.name,
#                             "score": float(similarity),
#                             "image_url": f"/uploads/pet_images/{target_pet.id}/main.jpg",
#                             "distance_km": float(distance_km) if distance_km else None,
#                             "description": target_pet.description,
#                             "date": target_pet.date.isoformat() if target_pet.date else None,
#                             "status": target_pet.status,
#                             "gender": target_pet.gender,
#                             "address": target_pet.address,
#                             "user": {
#                                 "id": user.id,
#                                 "name": user.name,
#                                 "profile_picture": user.profile_picture
#                             } if user else None
#                         })
        
#         matches.sort(key=lambda x: x["score"], reverse=True)
#         final_matches = matches[:limit]

#         # Fixed Notification Logic (4-5 arguments only)
#         for match in final_matches:
#             if match["score"] >= 0.8:
#                 # Notify source pet owner
#                 if not db.query(models.UserNotification).filter(
#                     models.UserNotification.user_id == source_pet.user_id,
#                     models.UserNotification.related_url == f"/pets/{match['pet_id']}",
#                     models.UserNotification.notification_type == "pet"
#                 ).first():
#                     notification_message = f"Found {match['name']} ({(match['score']*100):.1f}% match)"
#                     if match['distance_km']:
#                         notification_message += f" {match['distance_km']:.1f}km away"
                    
#                     db.add(models.UserNotification(
#                         user_id=source_pet.user_id,
#                         title=f"Potential {target_status} match",
#                         message=notification_message,
#                         notification_type="pet",
#                         related_url=f"/pets/{match['pet_id']}",
#                         created_at=datetime.utcnow()
#                     ))

#                 # Notify matching pet owner
#                 if match["user"] and not db.query(models.UserNotification).filter(
#                     models.UserNotification.user_id == match["user"]["id"],
#                     models.UserNotification.related_url == f"/pets/{pet_id}",
#                     models.UserNotification.notification_type == "pet"
#                 ).first():
#                     notification_message = f"Your pet matches {source_pet.name} ({(match['score']*100):.1f}% match)"
#                     if match['distance_km']:
#                         notification_message += f" {match['distance_km']:.1f}km away"
                    
#                     db.add(models.UserNotification(
#                         user_id=match["user"]["id"],
#                         title=f"Potential {source_status} match",
#                         message=notification_message,
#                         notification_type="pet",
#                         related_url=f"/pets/{pet_id}",
#                         created_at=datetime.utcnow()
#                     ))

#         # Existing search logging code remains unchanged
#         existing_search = db.query(PetSimilaritySearch).filter(
#             PetSimilaritySearch.source_pet_id == pet_id
#         ).first()
        
#         if existing_search:
#             existing_search.search_timestamp = datetime.utcnow()
#             existing_search.threshold = threshold
#             existing_search.max_distance = max_distance
#             existing_search.matches_found = len(final_matches)
#             existing_search.highest_similarity_score = final_matches[0]["score"] if final_matches else None
#             existing_search.was_successful = len(final_matches) > 0
#             existing_search.total_searches = existing_search.total_searches + 1
#         else:
#             search_record = PetSimilaritySearch(
#                 source_pet_id=pet_id,
#                 threshold=threshold,
#                 max_distance=max_distance,
#                 matches_found=len(final_matches),
#                 highest_similarity_score=final_matches[0]["score"] if final_matches else None,
#                 was_successful=len(final_matches) > 0,
#                 total_searches=1
#             )
#             db.add(search_record)
        
#         db.commit()
        
#         return {
#             "matches": final_matches,
#             "search_criteria": {
#                 "source_status": source_status,
#                 "target_status": target_status,
#                 "threshold": threshold,
#                 "message": f"Showing {target_status} pets that match your {source_status} pet" if final_matches else f"No matching {target_status} pets found"
#             }
#         }
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

 

# @router.get("/rehome/")
# async def get_rehome_pets(
#     type: Optional[str] = None,
#     gender: Optional[str] = None,
#     location: Optional[str] = None,
#     good_with: Optional[str] = None,
#     energy_level: Optional[str] = None,
#     user_id: Optional[int] = None,
#     skip: int = 0,
#     limit: int = 100,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Base query with joins
#         query = db.query(
#             models.Pet,
#             models.User.name.label("owner_name"),
#             models.User.phone_number.label("owner_phone"),
#             models.PetHealth  # Include PetHealth directly in the query
#         )\
#             .join(models.User, models.Pet.user_id == models.User.id)\
#             .outerjoin(models.PetHealth, models.Pet.id == models.PetHealth.pet_id)\
#             .filter(models.Pet.status == "Rehome Pet")\
#             .filter(models.Pet.is_published == True)\
#             .filter(models.Pet.admin_approved == True)
        
#         # Exclude user's own pets if user_id is provided
#         if user_id:
#             query = query.filter(models.Pet.user_id != user_id)
        
#         # Apply filters
#         if type:
#             query = query.filter(models.Pet.type.ilike(f"%{type}%"))
#         if gender:
#             query = query.filter(models.Pet.gender.ilike(f"%{gender}%"))
#         if location:
#             query = query.filter(models.Pet.address.ilike(f"%{location}%"))
        
#         # New filters for PetHealth fields
#         if good_with:
#             for trait in good_with.split(','):
#                 trait = trait.strip().lower()
#                 if trait == "children":
#                     query = query.filter(models.PetHealth.good_with_children == True)
#                 elif trait == "dogs":
#                     query = query.filter(models.PetHealth.good_with_dogs == True)
#                 elif trait == "cats":
#                     query = query.filter(models.PetHealth.good_with_cats == True)
#                 elif trait == "elderly":
#                     query = query.filter(models.PetHealth.good_with_elderly == True)
#                 elif trait == "strangers":
#                     query = query.filter(models.PetHealth.good_with_strangers == True)
        
#         if energy_level:
#             query = query.filter(models.PetHealth.energy_level.ilike(f"%{energy_level}%"))
        
#         # Execute query
#         results = query.offset(skip).limit(limit).all()
            
#         return [{
#             "id": pet.id,
#             "name": pet.name,
#             "type": pet.type,
#             "gender": pet.gender,
#             "image": pet.image,
#             "location": pet.address,
#             "status": pet.status,
#             "additional_images": pet.additional_images,
#             "description": pet.description,
#             "date": pet.date.isoformat() if pet.date else None,
#             "latitude": pet.latitude,
#             "longitude": pet.longitude,
#             "user_id": pet.user_id,
#             "owner_info": {
#                 "name": owner_name,
#                 "phone": owner_phone
#             },
#             "health_info": {
#                 "vaccinated": health.vaccinated if health else None,
#                 "spayed_neutered": health.spayed_neutered if health else None,
#                 "good_with": {
#                     "children": health.good_with_children if health else None,
#                     "dogs": health.good_with_dogs if health else None,
#                     "cats": health.good_with_cats if health else None,
#                     "elderly": health.good_with_elderly if health else None,
#                     "strangers": health.good_with_strangers if health else None
#                 } if health else None,
#                 "energy_level": health.energy_level if health else None,
#                 "temperament_personality": health.temperament_personality if health else None,
#                 "reason_for_adoption": health.reason_for_adoption if health else None
#             }
#         } for pet, owner_name, owner_phone, health in results]  # Now includes health in unpacking

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/adoption-application")
# async def submit_adoption_application(
#     form_data: dict,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Validate required user_id
#         if 'user_id' not in form_data:
#             raise HTTPException(status_code=400, detail="user_id is required")
        
#         # Create new application
#         application = models.AdoptionForm(
#             user_id=form_data['user_id'],
#             full_name=form_data.get('full_name'),
#             contact_info=form_data.get('contact_info'),
#             housing_type=form_data.get('housing_type'),
#             landlord_allows_pets=form_data.get('landlord_allows_pets'),
#             household_members=form_data.get('household_members'),
#             pet_allergies=form_data.get('pet_allergies'),
#             allergy_types=form_data.get('allergy_types'),
#             primary_caregiver=form_data.get('primary_caregiver'),
#             expense_responsibility=form_data.get('expense_responsibility'),
#             daily_alone_time=form_data.get('daily_alone_time'),
#             alone_time_plan=form_data.get('alone_time_plan'),
#             emergency_care=form_data.get('emergency_care'),
#             current_pets=form_data.get('current_pets'),
#             past_pets=form_data.get('past_pets'),
#             past_pets_outcome=form_data.get('past_pets_outcome'),
#             adoption_reason=form_data.get('adoption_reason'),
#             household_agreement=form_data.get('household_agreement'),
#             household_disagreement_reason=form_data.get('household_disagreement_reason')
#         )
        
#         db.add(application)
#         db.commit()
        
#         return {
#             "success": True,
#             "message": "Application submitted successfully",
#             "application_id": application.id,
#             "status": application.status
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/user-adoption-applications/{user_id}")
# async def get_user_applications(
#     user_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         applications = db.query(models.AdoptionForm)\
#             .filter(models.AdoptionForm.user_id == user_id)\
#             .order_by(models.AdoptionForm.created_at.desc())\
#             .all()
            
#         return {
#             "success": True,
#             "data": [
#                 {
#                     "id": app.id,
#                     "status": app.status,
#                     "created_at": app.created_at.isoformat(),
#                     "full_name": app.full_name,
#                     "contact_info": app.contact_info
#                 } for app in applications
#             ]
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    


# # backend/app/routers/pet_router.py
# @router.get("/pet/{pet_id}/adoption-status")
# async def check_adoption_status(
#     pet_id: int,
#     user_id: int,  # Pass adopter's user_id as query parameter
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Check if user has approved application
#         approved_application = db.query(models.AdoptionForm)\
#             .filter(
#                 models.AdoptionForm.user_id == user_id,
#                 models.AdoptionForm.status == 'approved'
#             )\
#             .first()
        
#         if not approved_application:
#             return {"can_adopt": False, "reason": "No approved application"}
            
#         return {"can_adopt": True}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# @router.post("/pet/{pet_id}/adopt", status_code=status.HTTP_201_CREATED)
# async def adopt_pet(
#     pet_id: int,
#     user_id: int,  # Adopter's user_id
#     db: Session = Depends(get_db)
# ):
#     """
#     Submit or update an adoption request for a pet
#     - Creates new adoption record if none exists
#     - Updates existing record if request already pending
#     - Notifies both owner and adopter
#     """
#     try:
#         # Verify pet exists and get owner
#         pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
#         if not pet:
#             raise HTTPException(status_code=404, detail="Pet not found")
        
#         # Check if pet is already adopted
#         if pet.status.lower() == "adopted":
#             raise HTTPException(
#                 status_code=400,
#                 detail="This pet has already been adopted"
#             )

#         # Check if adoption record already exists
#         existing_adoption = db.query(models.AdoptedPet)\
#             .filter(models.AdoptedPet.pet_id == pet_id)\
#             .filter(models.AdoptedPet.adopter_id == user_id)\
#             .first()
        
#         if existing_adoption:
#             # Update existing record
#             existing_adoption.status = 'pending'
#             existing_adoption.updated_at = datetime.utcnow()
#             message = "Adoption request updated"
#             adoption_id = existing_adoption.id
#         else:
#             # Create new adoption record
#             adoption = models.AdoptedPet(
#                 pet_id=pet_id,
#                 owner_id=pet.user_id,
#                 adopter_id=user_id,
#                 status='pending',
#                 created_at=datetime.utcnow()
#             )
#             db.add(adoption)
#             db.flush()  # Get the ID before commit
#             message = "Adoption request submitted"
#             adoption_id = adoption.id

#         # Notify pet owner
#         create_notification(
#             db,
#             pet.user_id,
#             "New Adoption Request",
#             f"Someone wants to adopt {pet.name}",
#             "pet"
#         )

#         # Notify adopter
#         create_notification(
#             db,
#             user_id,
#             "Adoption Request Sent",
#             f"Your request to adopt {pet.name} has been submitted",
#             "pet"
#         )

#         db.commit()
        
#         return {
#             "success": True,
#             "message": message,
#             "adoption_id": adoption_id,
#             "pet_name": pet.name
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to process adoption: {str(e)}"
#         )


# @router.get("/adoptions/")
# async def get_user_adoptions(
#     user_id: int = Query(..., description="ID of the user to fetch adoptions for"),
#     role: str = Query(..., description="'owner' or 'adopter' to filter by role"),
#     status: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     try:
#         query = db.query(models.AdoptedPet)\
#             .join(models.Pet, models.AdoptedPet.pet_id == models.Pet.id)\
#             .join(models.User, models.AdoptedPet.owner_id == models.User.id)\
#             .outerjoin(models.AdoptionForm, models.AdoptionForm.user_id == models.AdoptedPet.adopter_id)
        
#         if role == "owner":
#             query = query.filter(models.AdoptedPet.owner_id == user_id)
#         elif role == "adopter":
#             query = query.filter(models.AdoptedPet.adopter_id == user_id)
        
#         if status:
#             query = query.filter(models.AdoptedPet.status == status)
        
#         adoptions = query.order_by(models.AdoptedPet.created_at.desc()).all()
        
#         result = []
#         for adoption in adoptions:
#             # Get adoption form (if exists)
#             adoption_form = None
#             if adoption.adopter and adoption.adopter.adoption_forms:
#                 adoption_form = adoption.adopter.adoption_forms[0]
            
#             adoption_data = {
#                 "id": adoption.id,
#                 "pet_id": adoption.pet_id,
#                 "pet_name": adoption.pet.name,
#                 "pet_image": adoption.pet.image,
#                 "pet_type": adoption.pet.type,
#                 "owner_id": adoption.owner_id,
#                 "owner_name": adoption.owner.name,
#                 "adopter_id": adoption.adopter_id,
#                 "adopter_name": db.query(models.User).filter(models.User.id == adoption.adopter_id).first().name,
#                 "status": adoption.status,
#                 "created_at": adoption.created_at.isoformat(),
#                 "updated_at": adoption.updated_at.isoformat() if adoption.updated_at else None,
#                 "adoption_form": {
#                     "id": adoption_form.id if adoption_form else None,
#                     "status": adoption_form.status if adoption_form else None,
#                     "created_at": adoption_form.created_at.isoformat() if adoption_form and adoption_form.created_at else None,
                    
#                     # Applicant Information
#                     "full_name": adoption_form.full_name if adoption_form else None,
#                     "contact_info": adoption_form.contact_info if adoption_form else None,
#                     "housing_type": adoption_form.housing_type if adoption_form else None,
#                     "landlord_allows_pets": adoption_form.landlord_allows_pets if adoption_form else None,
                    
#                     # Household Details
#                     "household_members": adoption_form.household_members if adoption_form else None,
#                     "pet_allergies": adoption_form.pet_allergies if adoption_form else None,
#                     "allergy_types": adoption_form.allergy_types if adoption_form else None,
                    
#                     # Pet Care Plan
#                     "primary_caregiver": adoption_form.primary_caregiver if adoption_form else None,
#                     "expense_responsibility": adoption_form.expense_responsibility if adoption_form else None,
#                     "daily_alone_time": adoption_form.daily_alone_time if adoption_form else None,
#                     "alone_time_plan": adoption_form.alone_time_plan if adoption_form else None,
#                     "emergency_care": adoption_form.emergency_care if adoption_form else None,
                    
#                     # Pet Experience
#                     "current_pets": adoption_form.current_pets if adoption_form else None,
#                     "past_pets": adoption_form.past_pets if adoption_form else None,
#                     "past_pets_outcome": adoption_form.past_pets_outcome if adoption_form else None,
                    
#                     # Adoption Readiness
#                     "adoption_reason": adoption_form.adoption_reason if adoption_form else None,
#                     "household_agreement": adoption_form.household_agreement if adoption_form else None,
#                     "household_disagreement_reason": adoption_form.household_disagreement_reason if adoption_form else None
#                 } if adoption_form else None
#             }
#             result.append(adoption_data)
        
#         return result
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.patch("/adoptions/{adoption_id}/status")
# async def update_adoption_status(
#     adoption_id: int,
#     status_data: dict = Body(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     Update adoption status (owner only)
#     Allowed statuses: pending, approved, rejected, completed
#     """
#     try:
#         status = status_data.get("status", "").lower()
#         valid_statuses = ["pending", "approved", "rejected", "cancelled", "completed"]
        
#         if status not in valid_statuses:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
#             )

#         adoption = db.query(models.AdoptedPet)\
#             .filter(models.AdoptedPet.id == adoption_id)\
#             .first()
            
#         if not adoption:
#             raise HTTPException(status_code=404, detail="Adoption record not found")

#         # Get related pet
#         pet = db.query(models.Pet).filter(models.Pet.id == adoption.pet_id).first()
        
#         # Update status
#         previous_status = adoption.status
#         adoption.status = status
#         adoption.updated_at = datetime.utcnow()

#         # Update pet status if adoption is approved
#         if status == "Approved" and pet:
#             pet.status = "Adopted"
#             pet.updated_at = datetime.utcnow()

#         db.commit()

#         # Notify both parties
#         status_message = {
#             "approved": "approved your adoption request for",
#             "rejected": "rejected your adoption request for",
#             "completed": "completed the adoption process for"
#         }.get(status, f"changed status to {status} for")

#         if status in status_message and pet:
#             # Notify adopter
#             create_notification(
#                 db,
#                 adoption.adopter_id,
#                 f"Adoption {status.capitalize()}",
#                 f"The owner has {status_message} {pet.name}",
#                 "pet"
#             )

#             # Notify owner
#             create_notification(
#                 db,
#                 adoption.owner_id,
#                 f"Adoption {status.capitalize()}",
#                 f"You've {status_message} {pet.name}",
#                 "pet"
#             )

#         return {
#             "success": True,
#             "message": f"Adoption status updated to {status}",
#             "adoption_id": adoption.id,
#             "pet_name": pet.name if pet else None,
#             "previous_status": previous_status
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to update adoption status: {str(e)}"
#         )

        
