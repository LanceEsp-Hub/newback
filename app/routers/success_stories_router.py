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
from supabase import create_client

router = APIRouter(prefix="/api/success-stories", tags=["success_stories"])

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_SUCCESS_BUCKET", "success-stories")

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase initialized successfully for success stories")
except Exception as e:
    print(f"Supabase init failed: {str(e)}")
    raise RuntimeError("Supabase initialization failed") from e

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
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only images are allowed")

            # Generate unique filename
            ext = Path(file.filename).suffix.lower()
            unique_name = f"story_{uuid.uuid4().hex}{ext}"
            content = await file.read()

            # Upload to Supabase
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=unique_name,
                file=content,
                file_options={"content-type": file.content_type, "x-upsert": "true"}
            )

            # Handle errors
            if res.get("error"):
                raise HTTPException(status_code=500, detail=res["error"]["message"])

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
        # Generate Supabase URLs for images
        image_urls = []
        if story.image_filenames:
            for filename in story.image_filenames:
                image_urls.append(f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}")
        
        result.append({
            "id": story.id,
            "name": story.name,
            "cat_name": story.cat_name,
            "story": story.story,
            "image_urls": image_urls,  # Now returns full URLs
            "image_filenames": story.image_filenames,  # Keep filenames for backend reference
            "created_at": story.created_at
        })
    return result










































# # backend\app\routers\success_stories_router.py

# from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.database.database import get_db
# from app.models import models
# from pathlib import Path
# import uuid
# import os
# from typing import List
# from datetime import datetime

# router = APIRouter(prefix="/api/success-stories", tags=["success_stories"])

# UPLOAD_DIR = Path("app/uploads/success_stories")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# @router.post("/")
# async def create_success_story(
#     name: str = Form(...),
#     cat_name: str = Form(...),
#     story: str = Form(...),
#     files: List[UploadFile] = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         filenames = []

#         for file in files:
#             ext = Path(file.filename).suffix
#             unique_name = f"{uuid.uuid4().hex}{ext}"
#             destination = UPLOAD_DIR / unique_name

#             with destination.open("wb") as buffer:
#                 content = await file.read()
#                 buffer.write(content)

#             filenames.append(unique_name)

#         new_story = models.SuccessStory(
#             name=name,
#             cat_name=cat_name,
#             story=story,
#             image_filenames=filenames,
#             created_at=datetime.utcnow()
#         )

#         db.add(new_story)
#         db.commit()
#         db.refresh(new_story)

#         return {"message": "Success story saved", "story_id": new_story.id}

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Error saving story: {str(e)}")

# @router.get("/")
# def get_success_stories(db: Session = Depends(get_db)):
#     stories = db.query(models.SuccessStory).order_by(models.SuccessStory.created_at.desc()).all()
#     result = []
#     for story in stories:
#         result.append({
#             "id": story.id,
#             "name": story.name,
#             "cat_name": story.cat_name,
#             "story": story.story,
#             "image_urls": story.image_filenames,  # Just the filenames
#             "created_at": story.created_at
#         })
#     return result
