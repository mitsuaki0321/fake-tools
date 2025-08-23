"""Data types conversion functions"""

from logging import getLogger

import maya.api.OpenMaya as om
import numpy as np

logger = getLogger(__name__)


def float_to_MVector(values: list[list[float]]) -> list[om.MVector]:
    """Convert a list of float values to MVector objects.

    Args:
        values (list[list[float]]): A list of float values.

    Returns:
        list[om.MVector]: A list of MVector objects.
    """
    return [om.MVector(v) for v in values]


def float_to_MPoint(values: list[list[float]]) -> list[om.MPoint]:
    """Convert a list of float values to MPoint objects.

    Args:
        values (list[list[float]]): A list of float values.

    Returns:
        list[om.MPoint]: A list of MPoint objects.
    """
    return [om.MPoint(v) for v in values]


def MVector_to_float(values: list[om.MVector]) -> list[list[float]]:
    """Convert a list of MVector objects to float values.

    Args:
        values (list[om.MVector]): A list of MVector objects.

    Returns:
        list[list[float]]: A list of float values.
    """
    return [[v.x, v.y, v.z] for v in values]


def MPoint_to_float(values: list[om.MPoint]) -> list[list[float]]:
    """Convert a list of MPoint objects to float values.

    Args:
        values (list[om.MPoint]): A list of MPoint objects.

    Returns:
        list[list[float]]: A list of float values.
    """
    return [[v.x, v.y, v.z] for v in values]


def MVector_to_np(values: list[om.MVector]) -> np.ndarray:
    """Convert a list of MVector objects to numpy arrays.

    Args:
        values (list[om.MVector]): A list of MVector objects.

    Returns:
        np.ndarray: A numpy array.
    """
    return np.array(MVector_to_float(values))


def MPoint_to_np(values: list[om.MPoint]) -> np.ndarray:
    """Convert a list of MPoint objects to numpy arrays.

    Args:
        values (list[om.MPoint]): A list of MPoint objects.

    Returns:
        np.ndarray: A numpy array.
    """
    return np.array(MPoint_to_float(values))
