from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.models import Address
from app.schemas.ecommerce_schemas import AddressCreate, AddressResponse

router = APIRouter(prefix="/api/address", tags=["address"])

@router.post("/", response_model=AddressResponse)
def create_address(address: AddressCreate, db: Session = Depends(get_db)):
    db_address = Address(**address.dict())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.get("/user/{user_id}", response_model=List[AddressResponse])
def get_addresses(user_id: int, db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == user_id).all()