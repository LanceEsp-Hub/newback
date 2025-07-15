# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.database.database import engine
# from app.models import models
# from pathlib import Path

# import os
# from starlette.middleware.sessions import SessionMiddleware
# from app.routers import (
#     auth_router, 
#     # user_router, 
#     google_auth_router, 
#     password_reset_router, 
#     pet_dashboard_router, 
#     pet_router,
#     user_router, notification_router,
#     message_router,
#     admin_router,
#     success_stories_router,
#     security_router
      
# )
# from fastapi.staticfiles import StaticFiles  # Add this import

# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)


# models.Base.metadata.create_all(bind=engine)

# app = FastAPI()

# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# origins = [
#     "http://localhost:3000",
#     "https://smart-pet-eta.vercel.app",
#     os.getenv("FRONTEND_URL", "http://localhost:3000"),
#     # Add Railway's preview URLs
#     "https://*.railway.app",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# # Include the routers
# app.include_router(user_router.router)  # Added user router

# app.include_router(auth_router.router, prefix="/api")
# app.include_router(user_router.router, prefix="/api")
# app.include_router(google_auth_router.router)
# app.include_router(password_reset_router.router, prefix="/api")
# app.include_router(pet_dashboard_router.router)
# app.include_router(notification_router.router)
# app.include_router(message_router.router)
# app.include_router(admin_router.router)
# app.include_router(success_stories_router.router)
# app.include_router(security_router.router)





# # backend/app/main.py (add this line with other router includes)
# app.include_router(pet_router.router)

# # Mount the static directory
# app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
# app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")


# # Add this at the end of backend/app/main.py
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=port,
#         reload=False,
#         workers=1
#     )

# @app.get("/")
# def health_check():
#     return {"status": "✅ FastAPI backend is running"}




#!/usr/bin/env python3
"""
Railway setup script for Pet Management API
Run this after deploying to Railway to set up the database
"""

import asyncio
import os
from sqlalchemy import create_engine, text
from app.database.database import Base, engine
from app.models.models import User, Pet, Message, Notification, SuccessStory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth_router, 
    user_router, 
    google_auth_router, 
    password_reset_router, 
    pet_dashboard_router, 
    pet_router,
    notification_router,
    message_router,
    admin_router,
    success_stories_router,
    security_router
      
)
from fastapi.staticfiles import StaticFiles  # Add this import
from pathlib import Path

SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
UPLOAD_DIR = Path("app/uploads/pet_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Updated CORS for Railway deployment - keeping your original localhost:3000
origins = [
    "http://localhost:3000",
    "https://smart-pet-eta.vercel.app",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),  # Added for Railway
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Add this line
)

# Include the routers - keeping all your original router includes
app.include_router(user_router.router)  # Added user router

app.include_router(auth_router.router, prefix="/api")
app.include_router(user_router.router, prefix="/api")
app.include_router(google_auth_router.router)
app.include_router(password_reset_router.router, prefix="/api")
app.include_router(pet_dashboard_router.router)
app.include_router(notification_router.router)
app.include_router(message_router.router)
app.include_router(admin_router.router)
app.include_router(success_stories_router.router)
app.include_router(security_router.router)

# backend/app/main.py (add this line with other router includes)
app.include_router(pet_router.router)

# Mount the static directory - keeping your original static file mounts
app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# Keeping your original health check
@app.get("/")
def health_check():
    return {"status": "✅ FastAPI backend is running"}

if __name__ == "__main__":
    print("🚀 Setting up Railway deployment...")
    
    # Check environment variables
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    # Run setup
    asyncio.run(setup_database())
    asyncio.run(create_admin_user())
    
    print("✅ Railway setup complete!")

    import uvicorn
    # Railway provides PORT environment variable, fallback to 8000 for local development
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )
