"""
Maya-specific functions for optionVar management.
"""

import json
from typing import Any

import maya.cmds as cmds


class ToolOptionSettings:
    """A class to save and read tool settings in optionVar."""

    def __init__(self, tool_name: str):
        """Initializes the ToolOptionSettings instance.

        Args:
            tool_name (str): The name of the tool.
        """
        self.tool_name = tool_name

    def __full_key(self, key: str) -> str:
        """Formats the key with the tool name.

        Args:
            key (str): The key to format.

        Returns:
            str: The formatted key.
        """
        return f"{self.tool_name}.{key}"

    def read(self, key: str, default: Any | None = None) -> Any:
        """Reads the specified key from the optionVar.

        Args:
            key (str): The key to read.
            default (Any, optional): The default value to return if the key does not exist. Defaults to None.

        Returns:
            Any: The value for the specified key. If the key does not exist, returns the default value.
        """
        full_key = self.__full_key(key)
        if not cmds.optionVar(exists=full_key):
            return default
        value = cmds.optionVar(q=full_key)
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def write(self, key: str, value: Any) -> None:
        """Writes the specified value to the optionVar.

        Args:
            key (str): The key to write.
            value (Any): The value to write. Must be JSON serializable.

        Raises:
            ValueError: If the value is not JSON serializable.
        """
        full_key = self.__full_key(key)
        try:
            value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError("Value must be JSON serializable.") from e
        cmds.optionVar(sv=(full_key, value))

    def delete(self, key: str) -> None:
        """Deletes the specified key from the optionVar.

        Args:
            key (str): The key to delete.

        Raises:
            KeyError: If the key does not exist.
        """
        full_key = self.__full_key(key)
        if not cmds.optionVar(exists=full_key):
            raise KeyError(f"Key '{key}' does not exist")
        cmds.optionVar(remove=full_key)

    def exists(self, key: str) -> bool:
        """Whether the specified key exists in the optionVar.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return cmds.optionVar(exists=self.__full_key(key))
