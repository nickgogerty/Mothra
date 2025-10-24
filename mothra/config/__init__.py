"""Configuration management for MOTHRA."""

from mothra.config.settings import Settings, get_settings

settings = get_settings()

__all__ = ["Settings", "settings", "get_settings"]
