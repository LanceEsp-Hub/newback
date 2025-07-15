#!/usr/bin/env python3
"""
Railway deployment setup script
Run this after deploying to Railway to set up initial data
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine
from app.models.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False

def verify_database_connection():
    """Verify database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Database connection verified!")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    logger.info("🚀 Starting Railway setup...")
    
    # Verify database connection
    if not verify_database_connection():
        sys.exit(1)
    
    # Setup database tables
    if not setup_database():
        sys.exit(1)
    
    logger.info("🎉 Railway setup completed successfully!")

if __name__ == "__main__":
    main()
