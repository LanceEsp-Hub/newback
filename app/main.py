# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # from app.database.database import engine
# # from app.models import models
# # from pathlib import Path

# # import os
# # from starlette.middleware.sessions import SessionMiddleware
# # from app.routers import (
# #     auth_router, 
# #     # user_router, 
# #     google_auth_router, 
# #     password_reset_router, 
# #     pet_dashboard_router, 
# #     pet_router,
# #     user_router, notification_router,
# #     message_router,
# #     admin_router,
# #     success_stories_router,
# #     security_router
      
# # )
# # from fastapi.staticfiles import StaticFiles  # Add this import

# # SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# # UPLOAD_DIR = Path("app/uploads/pet_images")
# # UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# # Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)


# # models.Base.metadata.create_all(bind=engine)

# # app = FastAPI()

# # app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# # origins = [
# #     "http://localhost:3000",
# #     "https://smart-pet-eta.vercel.app",
# #     os.getenv("FRONTEND_URL", "http://localhost:3000"),
# #     # Add Railway's preview URLs
# #     "https://*.railway.app",
# # ]

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=origins,
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# #     expose_headers=["*"]
# # )

# # # Include the routers
# # app.include_router(user_router.router)  # Added user router

# # app.include_router(auth_router.router, prefix="/api")
# # app.include_router(user_router.router, prefix="/api")
# # app.include_router(google_auth_router.router)
# # app.include_router(password_reset_router.router, prefix="/api")
# # app.include_router(pet_dashboard_router.router)
# # app.include_router(notification_router.router)
# # app.include_router(message_router.router)
# # app.include_router(admin_router.router)
# # app.include_router(success_stories_router.router)
# # app.include_router(security_router.router)





# # # backend/app/main.py (add this line with other router includes)
# # app.include_router(pet_router.router)

# # # Mount the static directory
# # app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# # app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
# # app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")


# # # Add this at the end of backend/app/main.py
# # if __name__ == "__main__":
# #     import uvicorn
# #     port = int(os.environ.get("PORT", 8000))
# #     uvicorn.run(
# #         "app.main:app",
# #         host="0.0.0.0",
# #         port=port,
# #         reload=False,
# #         workers=1
# #     )

# # @app.get("/")
# # def health_check():
# #     return {"status": "✅ FastAPI backend is running"}


# #!/usr/bin/env python3
# """
# Railway setup script for Pet Management API
# Run this after deploying to Railway to set up the database
# """

# import asyncio
# import os
# from sqlalchemy import create_engine, text
# from app.database.database import Base, engine
# from app.models import models
# from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from starlette.middleware.sessions import SessionMiddleware
# from app.routers import (
#     auth_router, 
#     user_router, 
#     google_auth_router, 
#     password_reset_router, 
#     pet_dashboard_router, 
#     pet_router,
#     notification_router,
#     message_router,
#     admin_router,
#     success_stories_router,
#     security_router
# )
# from pathlib import Path

# # Configuration
# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)
# Path("app/uploads/messages").mkdir(parents=True, exist_ok=True)

# # Create database tables
# models.Base.metadata.create_all(bind=engine)

# # Initialize FastAPI app
# app = FastAPI(
#     title="Pet Management API",
#     description="A comprehensive pet management system",
#     version="1.0.0"
# )

# # Add session middleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# # CORS configuration
# origins = [
#     "http://localhost:3000",
#     "https://smart-pet-eta.vercel.app",
#     os.getenv("FRONTEND_URL", "http://localhost:3000"),
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# # Include routers
# app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(user_router.router, prefix="/api/users", tags=["Users"])
# app.include_router(google_auth_router.router, prefix="/api/google-auth", tags=["Google Auth"])
# app.include_router(password_reset_router.router, prefix="/api/password-reset", tags=["Password Reset"])
# app.include_router(pet_dashboard_router.router, prefix="/api/pet-dashboard", tags=["Pet Dashboard"])
# app.include_router(pet_router.router, prefix="/api/pets", tags=["Pets"])
# app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])
# app.include_router(message_router.router, prefix="/api/messages", tags=["Messages"])
# app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
# app.include_router(success_stories_router.router, prefix="/api/success-stories", tags=["Success Stories"])
# app.include_router(security_router.router, prefix="/api/security", tags=["Security"])

# # Static files
# app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
# app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# # Health check endpoints
# @app.get("/")
# def root():
#     return {"status": "✅ FastAPI backend is running", "message": "Pet Management API"}

# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "service": "pet-management-api"}

# # For Railway deployment
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





#!/usr/bin/env python3
"""
Railway setup script for Pet Management API
Run this after deploying to Railway to set up the database
"""

import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.database import Base, engine, get_db
from app.models import models
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
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
    security_router,
    file_upload_router
)
from app.core.config import settings
from pathlib import Path

# Configuration
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
UPLOAD_DIR = Path("app/uploads/pet_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)
Path("app/uploads/messages").mkdir(parents=True, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    description="Pet Management API"
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router.router, prefix="/api/users", tags=["Users"])
app.include_router(google_auth_router.router, prefix="/api/auth/google", tags=["Google Auth"])
app.include_router(password_reset_router.router, prefix="/api/password-reset", tags=["Password Reset"])
app.include_router(pet_dashboard_router.router, prefix="/api/dashboard", tags=["Pet Dashboard"])
app.include_router(pet_router.router, prefix="/api/pets", tags=["Pets"])
app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(message_router.router, prefix="/api/messages", tags=["Messages"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
app.include_router(success_stories_router.router, prefix="/api/success-stories", tags=["Success Stories"])
app.include_router(security_router.router, prefix="/api/security", tags=["Security"])
app.include_router(file_upload_router.router, prefix="/api/files", tags=["File Uploads"])

# Static files
app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# Health check endpoints
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}

# Example of a root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Pet Management API!"}

# You can add more global dependencies or event handlers here
@app.on_event("startup")
async def startup_event():
    print("Application startup...")
    # Add any startup logic here, e.g., connect to external services

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown...")
    # Add any shutdown logic here, e.g., close database connections

# For Railway deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )
