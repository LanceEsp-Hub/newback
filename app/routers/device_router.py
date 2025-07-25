# from fastapi import APIRouter, HTTPException, Depends, status
# from sqlalchemy.orm import Session
# from datetime import datetime
# from pydantic import BaseModel, validator
# from typing import Optional
# from app.database.database import get_db
# from app.models.models import Device, Location
# from supabase import create_client
# import os

# router = APIRouter(prefix="/api/device", tags=["device"])

# # Initialize Supabase client
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# # Pydantic models for request/response validation
# class LocationCreate(BaseModel):
#     unique_code: str
#     latitude: float
#     longitude: float
#     timestamp: Optional[datetime] = None

#     @validator('latitude')
#     def validate_lat(cls, v):
#         if abs(v) > 90:
#             raise ValueError('Latitude must be between -90 and 90')
#         return v

#     @validator('longitude')
#     def validate_lon(cls, v):
#         if abs(v) > 180:
#             raise ValueError('Longitude must be between -180 and 180')
#         return v

# class DeviceResponse(BaseModel):
#     device_id: int
#     unique_code: str
#     is_active: bool
#     is_online: bool
#     last_seen: Optional[datetime] = None

# class LocationResponse(BaseModel):
#     location_id: int
#     device_id: int
#     latitude: float
#     longitude: float
#     timestamp: datetime

# @router.post("/location", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
# async def create_device_location(
#     location_data: LocationCreate,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Get current timestamp
#         timestamp = location_data.timestamp or datetime.utcnow()
        
#         # Find or create device
#         device = db.query(Device).filter(Device.unique_code == location_data.unique_code).first()
#         if not device:
#             device = Device(
#                 unique_code=location_data.unique_code,
#                 is_active=True,  # Auto-activate new devices
#                 last_seen=timestamp,
#                 is_online=True
#             )
#             db.add(device)
#             db.flush()  # Get the device_id before commit

#         # Update device status
#         device.last_seen = timestamp
#         device.is_online = True

#         # Create location
#         new_location = Location(
#             device_id=device.device_id,
#             latitude=location_data.latitude,
#             longitude=location_data.longitude,
#             timestamp=timestamp
#         )
#         db.add(new_location)
#         db.commit()
#         db.refresh(new_location)

#         # Optional Supabase sync (now with error handling)
#         try:
#             supabase.table("xxlocation_db").insert({
#                 "device_id": device.device_id,
#                 "latitude": float(location_data.latitude),
#                 "longitude": float(location_data.longitude),
#                 "timestamp": str(timestamp)
#             }).execute()
#         except Exception as supabase_error:
#             print(f"Supabase sync failed (non-critical): {supabase_error}")

#         return new_location

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error processing location: {str(e)}"
#         )

# @router.get("/{unique_code}/locations", response_model=list[LocationResponse])
# async def get_device_locations(
#     unique_code: str,
#     limit: int = 100,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get location history for a device
#     """
#     device = db.query(Device).filter(Device.unique_code == unique_code).first()
#     if not device:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Device not found"
#         )

#     locations = db.query(Location)\
#         .filter(Location.device_id == device.device_id)\
#         .order_by(Location.timestamp.desc())\
#         .limit(limit)\
#         .all()

#     return locations

# @router.patch("/{unique_code}/status", response_model=DeviceResponse)
# async def update_device_status(
#     unique_code: str,
#     is_online: bool,
#     db: Session = Depends(get_db)
# ):
#     """
#     Update device online status
#     """
#     device = db.query(Device).filter(Device.unique_code == unique_code).first()
#     if not device:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Device not found"
#         )

#     device.is_online = is_online
#     device.last_seen = datetime.utcnow()
#     db.commit()
#     db.refresh(device)

#     return device



from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Optional
from app.database.database import get_db
from app.models.models import Device, Location
from supabase import create_client
import os

router = APIRouter(prefix="/api/device", tags=["device"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic models for request/response validation
class LocationCreate(BaseModel):
    unique_code: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None

    @validator('latitude')
    def validate_lat(cls, v):
        if abs(v) > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_lon(cls, v):
        if abs(v) > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class DeviceResponse(BaseModel):
    device_id: int
    unique_code: str
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None

class LocationResponse(BaseModel):
    location_id: int
    device_id: int
    latitude: float
    longitude: float
    timestamp: datetime

@router.post("/location", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_device_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db)
):
    try:
        # Get current timestamp
        timestamp = location_data.timestamp or datetime.utcnow()
        
        # Check if device exists in Supabase xxdevice_db
        supabase_device = supabase.table("xxdevice_db")\
            .select("*")\
            .eq("unique_code", location_data.unique_code)\
            .execute()
        
        if not supabase_device.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found in xxdevice_db"
            )
        
        # Get device from local database or create if not exists
        device = db.query(Device).filter(Device.unique_code == location_data.unique_code).first()
        if not device:
            device = Device(
                unique_code=location_data.unique_code,
                is_active=True,
                last_seen=timestamp,
                is_online=True
            )
            db.add(device)
            db.flush()

        # Update device status
        device.last_seen = timestamp
        device.is_online = True

        # Create location
        new_location = Location(
            device_id=device.device_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            timestamp=timestamp
        )
        db.add(new_location)
        db.commit()
        db.refresh(new_location)

        # Sync with Supabase xxlocation_db
        try:
            supabase.table("xxlocation_db").insert({
                "device_id": supabase_device.data[0]['device_id'],  # Use Supabase device ID
                "unique_code": location_data.unique_code,
                "latitude": float(location_data.latitude),
                "longitude": float(location_data.longitude),
                "timestamp": str(timestamp)
            }).execute()
        except Exception as supabase_error:
            print(f"Supabase sync failed (non-critical): {supabase_error}")

        return new_location

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing location: {str(e)}"
        )

@router.get("/{unique_code}/locations", response_model=list[LocationResponse])
async def get_device_locations(
    unique_code: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get location history for a device
    """
    device = db.query(Device).filter(Device.unique_code == unique_code).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    locations = db.query(Location)\
        .filter(Location.device_id == device.device_id)\
        .order_by(Location.timestamp.desc())\
        .limit(limit)\
        .all()

    return locations

@router.patch("/{unique_code}/status", response_model=DeviceResponse)
async def update_device_status(
    unique_code: str,
    is_online: bool,
    db: Session = Depends(get_db)
):
    """
    Update device online status
    """
    device = db.query(Device).filter(Device.unique_code == unique_code).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.is_online = is_online
    device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(device)

    return device
