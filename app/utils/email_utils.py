#backend\app\utils\email_utils.py

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from jinja2 import Template

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


print("MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
print("MAIL_PASSWORD:", os.getenv("MAIL_PASSWORD"))
print("MAIL_FROM:", os.getenv("MAIL_FROM"))
print("MAIL_PORT:", os.getenv("MAIL_PORT"))
print("MAIL_SERVER:", os.getenv("MAIL_SERVER"))

class EmailSchema(BaseModel):
    email: EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,  # Correct key
    MAIL_SSL_TLS=False,  # Correct key
    USE_CREDENTIALS=True
)

# async def send_verification_email(email: str, token: str):
#     verification_url = f"http://127.0.0.1:8000/api/verify-email?token={token}"

#     message = MessageSchema(
#         subject="Email Verification",
#         recipients=[email],
#         body=f"Click the link to verify your email: {verification_url}",
#         subtype="html",
#     )

#     fm = FastMail(conf)
#     await fm.send_message(message)

async def send_verification_email(email: str, token: str):
    # Generate verification URL that will redirect to login after verification
    verification_url = (
        f"{os.getenv('BACKEND_URL', 'https://smart-pet-backend-production.up.railway.app')}/api/verify-email?"
        f"token={token}&redirect_url={os.getenv('FRONTEND_LOGIN_URL', 'https://smart-pet-backend-production.up.railway.app/login')}"
    )
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Verify Your Email</title>
        <style>
            body { font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #7e22ce; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .logo { color: white; font-size: 24px; font-weight: bold; }
            .content { padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb; }
            .button { display: inline-block; padding: 12px 24px; background-color: #7e22ce; color: white; 
                     text-decoration: none; border-radius: 4px; font-weight: bold; margin: 20px 0; }
            .footer { margin-top: 30px; font-size: 12px; color: #6b7280; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">PetLove</div>
        </div>
        <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up with PetLove! To complete your registration, please verify your email address by clicking the button below:</p>
            
            <a href="{{ verification_url }}" class="button">Verify Email</a>
            
            <p>After verification, you'll be redirected to login page automatically.</p>
            
            <div class="footer">
                <p>© 2023 PetLove. All rights reserved.</p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all;"><a href="{{ verification_url }}">{{ verification_url }}</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(verification_url=verification_url)
    
    message = MessageSchema(
        subject="Please verify your email for PetLove",
        recipients=[email],
        body=html_content,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: str, reset_token: str):
    reset_url = f"https://smart-pet-backend-production.up.railway.app/reset-password?token={reset_token}"

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_url}",
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)
