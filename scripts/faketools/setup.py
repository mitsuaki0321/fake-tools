"""
Setup script for faketools.
"""

import logging


def setup_logger() -> None:
    """Setup root logger.

    Args:
        debug (bool): Whether to enable debug logging.
    """
    logger = logging.getLogger('faketools')

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)

    logger.propagate = False


def debug_mode(debug: bool) -> None:
    """Set debug mode.

    Args:
        debug (bool): Whether to enable debug logging.
    """
    logger = logging.getLogger('faketools')

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info(f'Debug mode: {debug}')
