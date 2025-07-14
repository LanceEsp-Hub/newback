import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if using one)
load_dotenv()

# Secret key for signing tokens
SECRET_KEY = os.getenv("SECRET_KEY", "asdasdasdsad")

# Email settings (modify as needed)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "pogisicj31@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "huqiwrsknzfyxqkh")
MAIL_FROM = os.getenv("MAIL_FROM", "nas@gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
