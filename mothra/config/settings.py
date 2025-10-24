"""
Configuration settings for MOTHRA using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="mothra", description="Database name")
    postgres_user: str = Field(default="mothra", description="Database user")
    postgres_password: str = Field(default="changeme", description="Database password")
    database_url: str | None = Field(default=None, description="Full database URL")

    @field_validator("database_url", mode="before")
    @classmethod
    def build_database_url(cls, v: str | None, info) -> str:
        """Build database URL if not provided."""
        if v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('postgres_user')}:"
            f"{data.get('postgres_password')}@{data.get('postgres_host')}:"
            f"{data.get('postgres_port')}/{data.get('postgres_db')}"
        )

    # Embedding Configuration (Local sentence-transformers)
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name"
    )
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension (384 for all-MiniLM-L6-v2)")

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")

    @property
    def redis_url(self) -> str:
        """Build Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Crawler Configuration
    max_concurrent_requests: int = Field(
        default=10, description="Max concurrent HTTP requests"
    )
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_backoff_factor: int = Field(default=2, description="Exponential backoff factor")

    # Rate Limiting (requests per minute)
    default_rate_limit: int = Field(default=50, description="Default rate limit")
    epa_rate_limit: int = Field(default=100, description="EPA API rate limit")
    ecoinvent_rate_limit: int = Field(default=10, description="Ecoinvent rate limit")

    # Monitoring
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "console"] = Field(
        default="json", description="Log output format"
    )

    # Data Storage
    data_dir: Path = Field(default=Path("./mothra/data"), description="Base data directory")
    raw_data_dir: Path = Field(
        default=Path("./mothra/data/raw"), description="Raw data directory"
    )
    processed_data_dir: Path = Field(
        default=Path("./mothra/data/processed"), description="Processed data directory"
    )
    cache_dir: Path = Field(
        default=Path("./mothra/data/cache"), description="Cache directory"
    )

    # Quality Thresholds
    min_quality_score: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum quality score"
    )
    min_confidence_level: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum confidence level"
    )
    dedup_similarity_threshold: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Deduplication similarity threshold"
    )

    # Orchestration
    enable_auto_updates: bool = Field(
        default=True, description="Enable automatic updates"
    )
    daily_update_cron: str = Field(
        default="0 2 * * *", description="Daily update cron expression"
    )
    weekly_refresh_cron: str = Field(
        default="0 2 * * SUN", description="Weekly refresh cron expression"
    )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.cache_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
