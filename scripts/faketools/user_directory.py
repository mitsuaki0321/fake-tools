"""User directory and settings management for faketools."""

import json
from logging import getLogger
import os

logger = getLogger(__name__)

SETTINGS_FILE_NAME = "settings"


class ToolDirectory:
    """Tool directory management."""

    _app_directory = os.environ.get("MAYA_APP_DIR", os.path.expanduser("~"))

    def __init__(self, module_name=None, create=True):
        """Initialize the tool directory.

        Args:
            module_name (str): The module name of the tool.
            create (bool): Whether to create the directory if it does not exist.
        """
        self._path = self._create_directory_path(module_name)
        if create and not os.path.exists(self._path):
            os.makedirs(self._path)

    def _create_directory_path(cls, module_name: str | None = None) -> str:
        """Create the tool directory path.

        Args:
            module_name (str): The module name of the tool.

        Returns:
            str: The tool directory path.
        """
        if not module_name:
            return os.path.normpath(os.path.join(cls._app_directory, __package__))
        else:
            module_path = module_name.split(".")
            return os.path.normpath(os.path.join(cls._app_directory, *module_path))

    def get_directory(self) -> str:
        """Get the tool directory.

        Returns:
            str: The tool directory.
        """
        return self._path

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._path}')"

    def __str__(self):
        return self._path


class ToolSettings:
    """Tool settings management."""

    def __init__(self, module_name=None):
        """Tool settings management.

        Args:
            module_name (str): The module name of the tool. If not provided, the global tool settings are used
        """
        self._directory = ToolDirectory(module_name).get_directory()

        if not module_name:
            self._file_name = f"{SETTINGS_FILE_NAME}.json"
        else:
            self._file_name = f"{module_name}_{SETTINGS_FILE_NAME}.json"

        self._settings_path = os.path.join(str(self._directory), self._file_name)

    def get_directory(self) -> str:
        """Get the tool directory.

        Returns:
            str: The tool directory.
        """
        return self._directory

    def get_file(self) -> str:
        """Get the settings file path.

        Returns:
            str: The settings file path.
        """
        return self._settings_path

    def exists_file(self) -> bool:
        """Check if the settings file exists.

        Returns:
            bool: True if the settings file exists, otherwise False.
        """
        return os.path.exists(self._settings_path)

    def load(self) -> dict:
        """Load the tool settings.

        Returns:
            dict: The tool settings.
        """
        if not os.path.exists(self._settings_path):
            return {}

        with open(self._settings_path) as f:
            settings = json.load(f)

        return settings

    def save(self, settings: dict):
        """Save the tool settings.

        Args:
            settings (dict): The tool settings.
        """
        if not isinstance(settings, dict):
            raise TypeError("Settings must be a dictionary.")

        with open(self._settings_path, "w") as f:
            json.dump(settings, f, indent=4)

        logger.debug(f"Saved settings to: {self._settings_path}")

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._settings_path}')"

    def __str__(self):
        return self._settings_path


def setup_global_settings() -> dict:
    """Setup global settings for the tool.

    Notes:
        - Creates a user settings file.
        - If a user settings file already exists, it merges with the tool's settings file.

    Returns:
        dict: The global settings.
    """
    tool_settings = ToolSettings()
    current_settings = tool_settings.load()

    package_directory = os.path.dirname(__file__)
    settings_file = os.path.join(package_directory, f"{SETTINGS_FILE_NAME}.json")

    if not os.path.exists(settings_file):
        raise FileNotFoundError(f"Settings file not found: {settings_file}")

    with open(settings_file) as f:
        settings = json.load(f)

    for key, value in current_settings.items():
        if key not in settings:
            settings[key] = value

    tool_settings.save(settings)

    logger.info(f"Loaded global settings from: {settings_file}")
