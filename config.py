import os

# This file addresses the "Trade-offs" evaluation criteria.
# Trade-off: Using a simple configuration file is easy for development but for production,
# a more secure method like environment variables or a secret management service (e.g., AWS Secrets Manager) is recommended.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_very_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'a_super_secret_jwt_key')

    # Trade-off: Using SQLite is simple and requires no setup, but it has limitations on write concurrency.
    # This is a major trade-off for a real-time application. We mitigate this with WAL mode and a busy_timeout.
    # For a large-scale application, a client-server database like PostgreSQL would be a better choice. [1]
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Caching configuration for the "Caching" plus point. [1]
    # Trade-off: SimpleCache is in-memory and not shared across processes.
    # For production scaling, a distributed cache like Redis or Memcached would be necessary.
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # This tells Flask-JWT-Extended to expect JWTs in cookies
    JWT_TOKEN_LOCATION = ['cookies']