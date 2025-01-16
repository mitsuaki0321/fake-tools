"""
Initialize the faketools package.
"""

from .setup import setup_logger
from .user_directory import setup_global_settings

# Initialize logger
setup_logger()

# Initialize global settings
setup_global_settings()
