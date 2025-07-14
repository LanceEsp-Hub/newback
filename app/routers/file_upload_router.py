# backend/app/routers/file_upload_router.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from datetime import datetime

router = APIRouter(prefix="/api/files", tags=["files"])

UPLOAD_DIR = "app/uploads/pet_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-pet-image")
async def upload_pet_image(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        return {
            "filename": filename,
            "filepath": file_path,
            "size": len(content)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )