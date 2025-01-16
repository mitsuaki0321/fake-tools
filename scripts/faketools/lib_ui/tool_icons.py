"""
Icons for the tools.
"""

import pathlib


def get_icon_path(picture_name: str) -> str:
    """Get the icon path.

    Args:
        picture_name (str): The name of the icon including the extension.

    Returns:
        str: The icon path.
    """
    icon_path = pathlib.Path(__file__).parent / 'icons' / f'{picture_name}.png'
    if not icon_path.exists():
        raise FileNotFoundError(f'Icon not found: {icon_path}')

    return icon_path.as_posix()
