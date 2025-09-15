"""Configuration management for the application."""

from typing import Any, Dict, Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    API_V1_STR: str = ""
    PROJECT_NAME: str = "Project Management API"
    VERSION: str = "0.5.0"
    DESCRIPTION: str = "API for managing projects, sprints, tasks, users and service centers"

    # Database
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017/project_management",
        description="MongoDB connection URL"
    )
    DATABASE_NAME: str = Field(
        default="project_management",
        description="Database name"
    )

    # Backward compatibility with existing environment variables
    MONGO_URI: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Server
    HOST: str = Field(default="0.0.0.0", description="Host to bind the server")
    PORT: int = Field(default=8000, description="Port to bind the server")
    SERVER_PORT: Optional[int] = None  # Compatibility
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # Additional settings for compatibility
    POPULATE_DB: bool = Field(default=False, description="Populate database on startup")
    RETRIES: int = Field(default=5, description="Number of retries for operations")
    AUTH_SERVICE_URL: Optional[str] = Field(default=None, description="Authentication service URL")
    USE_MIDDLEWARE: bool = Field(default=False, description="Use authentication middleware")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v if isinstance(v, list) else [v]
        return []

    def __init__(self, **kwargs):
        """Initialize settings with backward compatibility."""
        super().__init__(**kwargs)

        # Handle backward compatibility
        if self.MONGO_URI and not kwargs.get('MONGODB_URL'):
            if self.DB_NAME:
                self.MONGODB_URL = f"{self.MONGO_URI.rstrip('/')}/{self.DB_NAME}"
            else:
                self.MONGODB_URL = self.MONGO_URI

        if self.DB_NAME and not kwargs.get('DATABASE_NAME'):
            self.DATABASE_NAME = self.DB_NAME

        if self.SERVER_PORT and not kwargs.get('PORT'):
            self.PORT = self.SERVER_PORT

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields for backward compatibility
        extra = "allow"


settings = Settings()