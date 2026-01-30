import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_ENV', 'development') == 'development'
    DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'  # Set to 'false' in production
