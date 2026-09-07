import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "event_platform")

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@example.com")

    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM = os.getenv("TWILIO_FROM")
