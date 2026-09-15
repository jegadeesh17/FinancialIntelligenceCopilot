"""Central configuration loaded from environment variables.

Re-exports Settings and get_settings from configs.settings for backward compatibility
and adherence to PRODUCTION_ENGINEERING_STANDARDS.
"""

from configs.settings import PROJECT_ROOT, Settings, get_settings

__all__ = ["PROJECT_ROOT", "Settings", "get_settings"]
