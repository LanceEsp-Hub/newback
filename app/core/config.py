import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if using one)
load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres.fkpimtcxncgwtdsfyrjb:lance@aws-0-us-east-2.pooler.supabase.com:6543/postgres")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "asdasdasdsad")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email settings
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "pogisicj31@gmail.com")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "huqiwrsknzfyxqkh")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "nas@gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "653397573990-30qo6aca71lgldvilfhktc08n3280qhn.apps.googleusercontent.com")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "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")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://fkpimtcxncgwtdsfyrjb.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZrcGltdGN4bmNnd3Rkc2Z5cmpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2OTQyODEsImV4cCI6MjA2ODI3MDI4MX0.vZWZNOGRekiuudIQM1RM9dNAJy8dRcjXU6pglwcyPm4")
    
    # Environment
    ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT", "production")
    
    # App settings
    APP_NAME: str = "Pet Adoption API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ALLOWED_HOSTS: list = ["*"]  # Configure as needed for production

settings = Settings()
