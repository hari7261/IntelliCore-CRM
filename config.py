import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chat.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
      # Selenium
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '')  # Get from .env or leave empty for auto-detection
    HEADLESS = True
    