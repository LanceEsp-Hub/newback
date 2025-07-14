# backend\app\routers\success_stories_router.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
from pathlib import Path
import uuid
import os
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/success-stories", tags=["success_stories"])

UPLOAD_DIR = Path("app/uploads/success_stories")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/")
async def create_success_story(
    name: str = Form(...),
    cat_name: str = Form(...),
    story: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    try:
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

        return {"message": "Success story saved", "story_id": new_story.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving story: {str(e)}")

@router.get("/")
def get_success_stories(db: Session = Depends(get_db)):
    stories = db.query(models.SuccessStory).order_by(models.SuccessStory.created_at.desc()).all()
    result = []
    for story in stories:
        result.append({
            "id": story.id,
            "name": story.name,
            "cat_name": story.cat_name,
            "story": story.story,
            "image_urls": story.image_filenames,  # Just the filenames
            "created_at": story.created_at
        })
    return result
