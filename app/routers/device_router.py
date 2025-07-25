from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
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
        # Find device
        device = db.query(Device).filter(Device.unique_code == location_data.unique_code).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        # Update device
        device.last_seen = location_data.timestamp or datetime.utcnow()
        device.is_online = True

        # Create location
        new_location = Location(
            device_id=device.device_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            timestamp=location_data.timestamp or datetime.utcnow()
        )
        db.add(new_location)
        db.commit()
        db.refresh(new_location)

        # Optional Supabase sync
        try:
            supabase.table("xxlocation_db").insert({
                "device_id": device.device_id,
                "latitude": float(location_data.latitude),  # Explicit float
                "longitude": float(location_data.longitude),
                "timestamp": str(location_data.timestamp or datetime.utcnow())
            }).execute()
        except Exception as supabase_error:
            print(f"Supabase sync failed: {supabase_error}")
            # Don't fail the request, just log the error

        return new_location

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating location: {str(e)}"
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
