


# #!/usr/bin/env python3
# """
# Railway setup script for Pet Management API
# Run this after deploying to Railway to set up the database
# """

# import asyncio
# import os
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import Session
# from typing import Annotated
# from app.database.database import Base, engine, get_db
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
#     security_router,
#     file_upload_router
# )
# from app.core.config import settings
# from pathlib import Path

# # Configuration
# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)
# Path("app/uploads/messages").mkdir(parents=True, exist_ok=True)

# # Create database tables
# Base.metadata.create_all(bind=engine)

# # Initialize FastAPI app
# app = FastAPI(
#     title=settings.APP_NAME,
#     debug=settings.DEBUG,
#     version="1.0.0",
#     description="Pet Adoption Platform API with AI features"
# )

# # Add session middleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(user_router.router, prefix="/api/users", tags=["Users"])
# app.include_router(google_auth_router.router, prefix="/api/auth/google", tags=["Google Auth"])
# app.include_router(password_reset_router.router, prefix="/api/password", tags=["Password Reset"])
# app.include_router(pet_dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
# app.include_router(pet_router.router, prefix="/api/pets", tags=["Pets"])
# app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])
# app.include_router(message_router.router, prefix="/api/messages", tags=["Messages"])
# app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
# app.include_router(success_stories_router.router, prefix="/api/stories", tags=["Success Stories"])
# app.include_router(security_router.router, prefix="/api/security", tags=["Security"])
# app.include_router(file_upload_router.router, prefix="/api/upload", tags=["File Upload"])

# # Static files
# app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
# app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# # Health check endpoints
# @app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
# async def health_check():
#     """
#     Health check endpoint to verify the API is running.
#     """
#     return {"status": "healthy", "message": "Pet Adoption API is running"}

# # Example of a root endpoint
# @app.get("/", tags=["Root"])
# async def read_root():
#     return {"message": "Welcome to Pet Adoption API", "docs": "/docs"}

# # You can add more global dependencies or event handlers here
# @app.on_event("startup")
# async def startup_event():
#     print("Application startup...")
#     # Add any startup logic here, e.g., connect to external services

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Application shutdown...")
#     # Add any shutdown logic here, e.g., close database connections

# # Exception handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={"detail": f"Internal server error: {str(exc)}"}
#     )

# # For Railway deployment
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app,                     # ← Directly run the app object
#         host="0.0.0.0",
#         port=int(os.environ.get("PORT", 8000))
#     )


















# #!/usr/bin/env python3
# """
# FastAPI Pet Management Application
# """

# import os
# from sqlalchemy import text
# from typing import Annotated
# from .database.database import Base, engine, get_db
# from .models import models
# from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import JSONResponse
# from starlette.middleware.sessions import SessionMiddleware
# from .routers import (
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
#     security_router,
#     file_upload_router,
#     device_router
# )
# from .core.config import settings
# from pathlib import Path

# # Configuration
# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)
# Path("app/uploads/messages").mkdir(parents=True, exist_ok=True)

# # Create database tables
# Base.metadata.create_all(bind=engine)

# # Initialize FastAPI app
# app = FastAPI(
#     title=settings.APP_NAME,
#     debug=settings.DEBUG,
#     version="1.0.0",
#     description="Pet Adoption Platform API with AI features"
# )

# # Add session middleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# # app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(auth_router.router, prefix="/api")
# app.include_router(auth_router.router, prefix="/api")
# app.include_router(user_router.router)
# app.include_router(pet_router.router)

# app.include_router(google_auth_router.router)
# app.include_router(password_reset_router.router, prefix="/api")
# app.include_router(pet_dashboard_router.router)
# app.include_router(notification_router.router)
# app.include_router(message_router.router)
# app.include_router(admin_router.router)
# app.include_router(success_stories_router.router)
# app.include_router(security_router.router)

# app.include_router(device_router.router)


# # app.include_router(user_router.router, prefix="/api/users", tags=["Users"])
# # app.include_router(google_auth_router.router, prefix="/api/auth/google", tags=["Google Auth"])
# # app.include_router(password_reset_router.router, prefix="/api/password", tags=["Password Reset"])
# # app.include_router(pet_dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
# # app.include_router(pet_router.router, prefix="/api/pets", tags=["Pets"])
# # app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])
# # app.include_router(message_router.router, prefix="/api/messages", tags=["Messages"])
# # app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
# # app.include_router(success_stories_router.router, prefix="/api/stories", tags=["Success Stories"])
# # app.include_router(security_router.router, prefix="/api/security", tags=["Security"])
# # app.include_router(file_upload_router.router, prefix="/api/upload", tags=["File Upload"])

# # Static files
# app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
# app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# # Health check endpoints - Railway specific
# @app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
# async def health_check():
#     """
#     Health check endpoint to verify the API is running.
#     Railway will query this endpoint during deployment.
#     """
#     try:
#         # Test database connection
#         with engine.connect() as connection:
#             connection.execute(text("SELECT 1"))
        
#         return {
#             "status": "healthy", 
#             "message": "Pet Adoption API is running",
#             "database": "connected",
#             "port": os.environ.get("PORT", "unknown")
#         }
#     except Exception as e:
#         print(f"Health check failed: {str(e)}")
#         # Return 503 Service Unavailable if database is down
#         return JSONResponse(
#             status_code=503,
#             content={
#                 "status": "unhealthy",
#                 "message": "Database connection failed",
#                 "error": str(e)
#             }
#         )

# # Additional health check endpoint (alternative)
# @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health Check"])
# async def health_check_k8s():
#     """Alternative health check endpoint (Kubernetes style)"""
#     return {"status": "ok"}

# # Root endpoint
# @app.get("/", tags=["Root"])
# async def read_root():
#     return {
#         "message": "Welcome to Pet Adoption API", 
#         "docs": "/docs",
#         "health": "/health"
#     }

# # Startup and shutdown events
# @app.on_event("startup")
# async def startup_event():
#     print("🚀 Pet Adoption API starting up...")
#     print(f"📍 Port: {os.environ.get('PORT', 'Not set')}")
#     print(f"🔧 Environment: {'Development' if settings.DEBUG else 'Production'}")

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("👋 Pet Adoption API shutting down...")

# # Global exception handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     print(f"❌ Global exception: {str(exc)}")
#     return JSONResponse(
#         status_code=500,
#         content={"detail": f"Internal server error: {str(exc)}"}
#     )

# # For Railway deployment and local development
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     print(f"🚀 Starting server on port {port}")
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=port,
#         log_level="info",
#         reload=False  # Set to True for local development
#     )

#!/usr/bin/env python3
"""
FastAPI Pet Management Application
"""

import os
from sqlalchemy import text
from typing import Annotated
from .database.database import Base, engine, get_db
from .models import models
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from .routers import (
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
    ecommerce_router,
    address_router,
    checkout_router,
    voucher_router,
    file_upload_router,
    device_router
)
from .core.config import settings
from pathlib import Path

# Configuration
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path("app/uploads/pet_images").mkdir(parents=True, exist_ok=True)
Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)
Path("app/uploads/messages").mkdir(parents=True, exist_ok=True)
Path("app/uploads/profile_pictures").mkdir(parents=True, exist_ok=True)
Path("app/uploads/products").mkdir(parents=True, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME if hasattr(settings, 'APP_NAME') else "Pet Adoption Platform",
    debug=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
    version="1.0.0",
    description="Pet Adoption Platform API with AI features"
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS configuration
origins = [
    "http://localhost:3000",
    "https://smart-pet-eta.vercel.app",
    "https://smart-pet-frontend.vercel.app",
    "https://smart-pet-git-main-swift-2024.vercel.app",
    settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000"
]

# Remove duplicates and filter out None values
origins = list(set([origin for origin in origins if origin]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include all routers
app.include_router(user_router.router)
app.include_router(auth_router.router, prefix="/api")
app.include_router(google_auth_router.router)
app.include_router(password_reset_router.router, prefix="/api")
app.include_router(pet_dashboard_router.router)
app.include_router(notification_router.router)
app.include_router(message_router.router)
app.include_router(admin_router.router)
app.include_router(success_stories_router.router)
app.include_router(security_router.router)
app.include_router(pet_router.router)
app.include_router(ecommerce_router.router)
app.include_router(address_router.router)
app.include_router(checkout_router.router)
app.include_router(voucher_router.router)

# Include optional routers if they exist
try:
    app.include_router(device_router.router)
except NameError:
    pass  # device_router not available

try:
    app.include_router(file_upload_router.router)
except NameError:
    pass  # file_upload_router not available

# Mount static directories
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")

# Health check endpoints - Railway specific
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    Railway will query this endpoint during deployment.
    """
    try:
        # Test database connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        return {
            "status": "healthy", 
            "message": "Pet Adoption API is running",
            "database": "connected",
            "port": os.environ.get("PORT", "unknown")
        }
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        # Return 503 Service Unavailable if database is down
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Database connection failed",
                "error": str(e)
            }
        )

# Additional health check endpoint (alternative)
@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health Check"])
async def health_check_k8s():
    """Alternative health check endpoint (Kubernetes style)"""
    return {"status": "ok"}

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to Pet Adoption API", 
        "docs": "/docs",
        "health": "/health"
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    print("🚀 Pet Adoption API starting up...")
    print(f"📍 Port: {os.environ.get('PORT', 'Not set')}")
    print(f"🔧 Environment: {'Development' if (hasattr(settings, 'DEBUG') and settings.DEBUG) else 'Production'}")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Pet Adoption API shutting down...")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"❌ Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# For Railway deployment and local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False  # Set to True for local development
    )
