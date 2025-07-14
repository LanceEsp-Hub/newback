#backend\app\main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine
from app.models import models
from pathlib import Path

import os
from starlette.middleware.sessions import SessionMiddleware
from app.routers import (
    auth_router, 
    # user_router, 
    google_auth_router, 
    password_reset_router, 
    pet_dashboard_router, 
    pet_router,
    user_router, notification_router,
    message_router,
    admin_router,
    success_stories_router,
    security_router
      
)
from fastapi.staticfiles import StaticFiles  # Add this import

SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
UPLOAD_DIR = Path("app/uploads/pet_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path("app/uploads/success_stories").mkdir(parents=True, exist_ok=True)


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Add this line

)

# Include the routers
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

# Mount the static directory
app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
app.mount("/uploads/success_stories", StaticFiles(directory="app/uploads/success_stories"), name="stories_images")


# Add this at the end of backend/app/main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        workers=1
    )

@app.get("/")
def health_check():
    return {"status": "✅ FastAPI backend is running"}









































# # backend\app\main.py

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.database.database import engine
# from app.models import models
# from pathlib import Path
# import os
# from starlette.middleware.sessions import SessionMiddleware
# from app.routers import (
#     auth_router, 
#     google_auth_router, 
#     password_reset_router, 
#     pet_dashboard_router, 
#     pet_router,
#     user_router, 
#     notification_router,
#     message_router,
#     admin_router      
# )
# from fastapi.staticfiles import StaticFiles

# # Configuration
# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# # Create database tables
# models.Base.metadata.create_all(bind=engine)

# # Initialize FastAPI app
# app = FastAPI()

# # Middleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)



# # CORS configuration
# origins = [
#     "http://localhost:3000",
#     "https://smart-pet-eta.vercel.app",
#     "https://smart-pet-eta.vercel.app",  # Both with and without colon for compatibility
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
# app.include_router(auth_router.router, prefix="/api")
# app.include_router(user_router.router, prefix="/api")
# app.include_router(google_auth_router.router, prefix="/api")
# app.include_router(password_reset_router.router, prefix="/api")
# app.include_router(pet_dashboard_router.router, prefix="/api")
# app.include_router(notification_router.router, prefix="/api")
# app.include_router(message_router.router, prefix="/api")
# app.include_router(admin_router.router, prefix="/api")
# app.include_router(pet_router.router, prefix="/api")

# # Static files
# app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
# app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")


# import os
# print(f"🚀 Starting app... PORT={os.environ.get('PORT', 'NOT SET')}")

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.database.database import engine
# from app.models import models
# from pathlib import Path
# from starlette.middleware.sessions import SessionMiddleware

# print("📦 Imports loaded successfully")

# from app.routers import (
#     auth_router, 
#     google_auth_router, 
#     password_reset_router, 
#     pet_dashboard_router, 
#     pet_router,
#     user_router, 
#     notification_router,
#     message_router,
#     admin_router      
# )
# from fastapi.staticfiles import StaticFiles

# print("🔌 Routers imported successfully")

# # Configuration
# SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "asdasdasdsad")
# UPLOAD_DIR = Path("app/uploads/pet_images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# print("📁 Upload directories created")

# # Create database tables
# try:
#     models.Base.metadata.create_all(bind=engine)
#     print("✅ Database tables created")
# except Exception as e:
#     print(f"❌ Database error: {e}")

# # Initialize FastAPI app
# app = FastAPI()
# print("🎯 FastAPI app initialized")

# # Middleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# # CORS configuration
# origins = [
#     "http://localhost:3000",
#     "https://smart-pet-eta.vercel.app",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# print("🔒 Middleware configured")

# # Include routers
# try:
#     app.include_router(auth_router.router, prefix="/api")
#     app.include_router(user_router.router, prefix="/api")
#     app.include_router(google_auth_router.router, prefix="/api")
#     app.include_router(password_reset_router.router, prefix="/api")
#     app.include_router(pet_dashboard_router.router, prefix="/api")
#     app.include_router(notification_router.router, prefix="/api")
#     app.include_router(message_router.router, prefix="/api")
#     app.include_router(admin_router.router, prefix="/api")
#     app.include_router(pet_router.router, prefix="/api")
#     print("🛣️  All routers included successfully")
# except Exception as e:
#     print(f"❌ Router error: {e}")

# # Static files
# try:
#     app.mount("/uploads/pet_images", StaticFiles(directory="app/uploads/pet_images"), name="pet_images")
#     app.mount("/uploads/messages", StaticFiles(directory="app/uploads/messages"), name="message_images")
#     print("📸 Static files mounted")
# except Exception as e:
#     print(f"❌ Static files error: {e}")

# @app.get("/")
# async def health_check():
#     return {"status": "healthy", "message": "Pet API is running!"}

# print("🎉 App setup complete - ready to serve!")