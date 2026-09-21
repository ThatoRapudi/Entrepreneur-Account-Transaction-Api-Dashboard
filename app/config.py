"""
Configuration Management
Reads environment variables from .env file
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration.
    Automatically reads values from .env file.
    
    Why we need this:
    - Centralized config management
    - Sensitive data (passwords, keys) stored in .env
    - Easy to change settings without editing code
    """
    
    # Database Configuration - defaults to local SQLite so this runs
    # with zero setup; docker-compose.yml overrides this to Postgres.
    DATABASE_URL: str = "sqlite:///./entrepreneur.db"
    DATABASE_NAME: str = "entrepreneur_db"

    # JWT Configuration - the default below is a demo-only value with no
    # connection to any real system, checked into this public repo on
    # purpose so the project runs with zero setup. Anyone deploying this
    # for real must override it via an actual .env (never commit that
    # one) - see .env.example and PRODUCTION_DEPLOYMENT.md.
    SECRET_KEY: str = "sCsAeYoxbqP7Wu2Lk_gh5K_GT6_a6Nach8e8LX4gztKOnn-YmiDOldI6yidwfJ4m"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Dashboard login gate (single admin account, not real SSO - see
    # app/auth.py). Same demo-only reasoning as SECRET_KEY above.
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Demo-Review-2026"

    # API Configuration
    DEBUG: bool = False
    API_TITLE: str = "Entrepreneur Account Aggregation API"
    API_VERSION: str = "1.0.0"

    # Deployed frontend origin(s) for CORS, e.g. "https://dashboard.example.com".
    # Comma-separated if there's more than one (staging + prod, say). Local
    # dev origins (localhost/127.0.0.1, any port) are always allowed via
    # regex in main.py regardless of this setting - this is only for a
    # real deployed frontend URL once one exists.
    FRONTEND_URL: str = ""
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"  # Read from .env file
        case_sensitive = True  # Variables are case-sensitive
        # .env now also carries Docker/Postgres-only variables
        # (POSTGRES_USER/PASSWORD/DB, VITE_API_BASE_URL) that
        # docker-compose.yml reads for its own variable substitution -
        # this app never uses them directly, so without "ignore" here,
        # pydantic-settings rejects the whole file on startup just for
        # containing keys this Settings class doesn't declare.
        extra = "ignore"


# Global settings instance
# Used throughout the app: from app.config import settings
settings = Settings()