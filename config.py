import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'a_super_secret_jwt_key')

    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # This tells Flask-JWT-Extended to expect JWTs in cookies
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    # Default is 30 days.
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)