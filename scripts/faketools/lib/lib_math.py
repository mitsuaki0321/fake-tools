"""
Math functions.
"""

import math
from logging import getLogger

import maya.api.OpenMaya as om
from numpy import array, linalg, linspace
from scipy.interpolate import Rbf

logger = getLogger(__name__)


# Utilities

def round_up(value, decimal_places=0) -> float:
    """Round up the value.

    Args:
        value: The value to round up.
        decimal_places: The number of decimal places. Default is 0.

    Returns:
        float: The rounded up value.
    """
    factor = 10 ** decimal_places
    return math.ceil(value * factor) / factor


def round_down(value, decimal_places=0) -> float:
    """Round down the value.

    Args:
        value: The value to round down.
        decimal_places: The number of decimal places. Default is 0.

    Returns:
        float: The rounded down value.
    """
    factor = 10 ** decimal_places
    return math.floor(value * factor) / factor


# Distance


def get_distance(point_a: list[float], point_b: list[float]) -> float:
    """Get the distance between two points.

    Args:
        point_a (list[float]): The first point.
        point_b (list[float]): The second point.

    Returns:
        float: The distance.
    """
    distance = float(linalg.norm(array(point_a) - array(point_b)))

    logger.debug(f'Distance: {distance}')

    return distance


def inner_divide(point_a: list[float], point_b: list[float], spans: int = 1) -> list[list[float]]:
    """Divide the line segment.

    Args:
        point_a (list[float]): The first point.
        point_b (list[float]): The second point.
        spans (int): The number of spans. Default is 1.

    Returns:
        list[list[float]]: The divided points.
    """
    divided_points = array([linspace(a, b, spans + 1) for a, b in zip(point_a, point_b)]).T.tolist()

    logger.debug(f'Inner divided points: {divided_points}')

    return divided_points


# Object Position

def get_bounding_box(points: list[list[float]]) -> tuple[list[float], list[float]]:
    """Get the bounding box from a list of 3D points.

    Args:
        points (list[list[float]]): List of 3D points.

    Returns:
        tuple[list[float], list[float]]: Minimum point and maximum point of the bounding box.
    """
    points_array = array(points)
    min_point = points_array.min(axis=0).tolist()
    max_point = points_array.max(axis=0).tolist()

    logger.debug(f'Bounding box: {min_point}, {max_point}')

    return min_point, max_point


def get_bounding_box_center(points: list[list[float]]) -> list[float]:
    """Get the center point of the bounding box from a list of 3D points.

    Args:
        points (list[list[float]]): List of 3D points.

    Returns:
        list[float]: Coordinates of the center point.
    """
    min_point, max_point = get_bounding_box(points)
    center_point = [(min_val + max_val) / 2 for min_val, max_val in zip(min_point, max_point)]

    logger.debug(f'Bounding box center: {center_point}')

    return center_point


def get_centroid(points: list[list[float]]) -> list[float]:
    """Get the centroid coordinates of a set of 3D points.

    Args:
        points (list[list[float]]): List of 3D points.

    Returns:
        list[float]: Coordinates of the centroid.
    """
    points_array = array(points)
    centroid = points_array.mean(axis=0).tolist()

    logger.debug(f'Centroid: {centroid}')

    return centroid


# Vector

def get_vector(point_a: list[float], point_b: list[float]) -> list[float]:
    """Get the vector from point A to point B.

    Args:
        point_a (list[float]): The first point.
        point_b (list[float]): The second point.

    Returns:
        list[float]: The vector.
    """
    vector = [(b - a) for a, b in zip(point_a, point_b)]

    logger.debug(f'Vector: {vector}')

    return vector


def get_vector_angle(vector_a: list[float], vector_b: list[float], as_euler: bool = False) -> float:
    """Get the angle between two vectors.

    Args:
        vector_a (list[float]): The first vector.
        vector_b (list[float]): The second vector.
        as_euler (bool): Return the angle as euler rotation. Default is False.

    Returns:
        float: The angle in degrees or radians.
    """
    vector_a = om.MVector(vector_a).normal()
    vector_b = om.MVector(vector_b).normal()

    angle = vector_a.angle(vector_b)
    if as_euler:
        angle = math.degrees(angle)

    logger.debug(f'Angle: {angle}')

    return angle


def vector_orthogonalize(vector_a: list[float], vector_b: list[float]) -> om.MVector:
    """Orthogonalize vector B to vector A.

    Args:
        vector_a (list[float]): The first vector.
        vector_b (list[float]): The second vector.

    Returns:
        om.MVector: The orthogonalized vector.
    """
    vector_a_normalized = om.MVector(vector_a).normal()
    vector_b = om.MVector(vector_b)

    vector_ortho = (vector_b - (vector_a_normalized * vector_b) * vector_a_normalized).normal()

    return vector_ortho


# Rotation


def mult_rotation(rotations: list[list[float]]) -> list[float]:
    """Multiply rotations.

    Args:
        rotations (list[list[float]]): List of euler rotations.

    Returns:
        list[float]: The multiplied rotation.
    """
    quat_rotation = om.MQuaternion()
    for rotation in rotations:
        quat_rotation *= om.MEulerRotation([math.radians(value) for value in rotation]).asQuaternion()

    quat_rotation.normalizeIt()
    euler_rotation = quat_rotation.asEulerRotation()
    euler_rotation_degree = [math.degrees(euler_rotation.x), math.degrees(euler_rotation.y), math.degrees(euler_rotation.z)]

    logger.debug(f'Multiplied rotation: {euler_rotation_degree}')

    return euler_rotation_degree


def invert_rotation(rotation: list[float]) -> list[float]:
    """Invert the rotation.

    Args:
        rotation (list[float]): The euler rotation.

    Returns:
        list[float]: The inverted rotation.
    """
    quat_rotation = om.MEulerRotation([math.radians(value) for value in rotation]).asQuaternion()
    quat_rotation.invertIt()

    euler_rotation = quat_rotation.asEulerRotation()
    euler_rotation_degree = [math.degrees(euler_rotation.x), math.degrees(euler_rotation.y), math.degrees(euler_rotation.z)]

    logger.debug(f'Inverted rotation: {euler_rotation_degree}')

    return euler_rotation_degree


def vector_to_rotation(primary_vec, secondary_vec, primary_axis='x', secondary_axis='y'):
    """Get the rotation from vector A to vector B.

    Args:
        primary_vec (Sequence[float]): The primary vector.
        secondary_vec (Sequence[float]): The secondary vector.
        primary_axis (str): The axis to align the primary vector ('x', 'y', 'z').
        secondary_axis (str): The axis to align the secondary vector ('x', 'y', 'z').

    Returns:
        list[float]: The rotation in degrees.

    Raises:
        ValueError: If primary_axis and secondary_axis are the same or invalid.
    """
    # Validate axis
    if primary_axis == secondary_axis:
        raise ValueError('Primary axis and secondary axis cannot be the same.')
    if primary_axis not in ['x', 'y', 'z'] or secondary_axis not in ['x', 'y', 'z']:
        raise ValueError('Invalid axis.')

    # Normalize vectors
    primary_vec = om.MVector(primary_vec).normal()
    secondary_vec = vector_orthogonalize(primary_vec, secondary_vec)
    third_vec = primary_vec ^ secondary_vec

    # Get rotation
    matrix = om.MMatrix([primary_vec.x, primary_vec.y, primary_vec.z, 0,
                        secondary_vec.x, secondary_vec.y, secondary_vec.z, 0,
                        third_vec.x, third_vec.y, third_vec.z, 0,
                        0, 0, 0, 1])

    offset_matrices = {
        ('x', 'y'): om.MMatrix(),
        ('x', 'z'): om.MMatrix([1, 0, 0, 0,
                                0, 0, -1, 0,
                                0, 1, 0, 0,
                                0, 0, 0, 1]),
        ('y', 'x'): om.MMatrix([0, 1, 0, 0,
                                1, 0, 0, 0,
                                0, 0, -1, 0,
                                0, 0, 0, 1]),
        ('y', 'z'): om.MMatrix([0, 0, 1, 0,
                                1, 0, 0, 0,
                                0, 1, 0, 0,
                                0, 0, 0, 1]),
        ('z', 'x'): om.MMatrix([0, 1, 0, 0,
                                0, 0, 1, 0,
                                1, 0, 0, 0,
                                0, 0, 0, 1]),
        ('z', 'y'): om.MMatrix([0, 0, -1, 0,
                                0, 1, 0, 0,
                                1, 0, 0, 0,
                                0, 0, 0, 1])
    }

    matrix = offset_matrices[(primary_axis, secondary_axis)] * matrix
    transform = om.MTransformationMatrix(matrix)
    euler_rotation = transform.rotation()

    result_rotation = [math.degrees(euler_rotation.x), math.degrees(euler_rotation.y), math.degrees(euler_rotation.z)]

    logger.debug(f'Vector to rotation: {result_rotation}')

    return result_rotation


def get_average_rotation(rotations: list[list[float]]) -> list[float]:
    """Get the average rotation from a list of rotations.

    Args:
        rotations (list[list[float]]): List of rotations.

    Returns:
        list[float]: The average rotation.
    """
    if len(rotations) == 0:
        return rotations[0]

    quats = [om.MEulerRotation(rotation).asQuaternion() for rotation in rotations]
    log_sum = om.MVector([0.0, 0.0, 0.0])
    for quat in quats:
        quat_log = quat.log()
        log_sum += om.MVector([quat_log.x, quat_log.y, quat_log.z])

    avg_log = log_sum / len(quats)
    avg_quat = om.MQuaternion(avg_log.x, avg_log.y, avg_log.z, 0).exp()
    avg_quat.normalize()

    avg_euler = avg_quat.asEulerRotation()
    avg_euler_degree = [math.degrees(avg_euler.x), math.degrees(avg_euler.y), math.degrees(avg_euler.z)]

    logger.debug(f'Average rotation: {avg_euler_degree}')

    return avg_euler_degree


# Mapping

def map_point_with_rbf(src_points: list[list[float]], dest_points: list[list[float]], target_point: list[float], **kwargs) -> list[float]:
    """Map a point from source point set A to target point set B using radial basis function.

    Args:
        src_points (list[list[float]]): Source point set A.
        dest_points (list[list[float]]): Target point set B.
        target_point (list[float]): The point to map.

    Keyword Args:
        function_type (str): The radial basis function to use ('linear', 'gaussian', 'thin_plate'). Default is 'linear'.

    Returns:
        list[float]: The corresponding value in point set B.
    """
    logger.debug(f'Source points: {src_points}')
    logger.debug(f'Destination points: {dest_points}')
    logger.debug(f'Target point: {target_point}')

    function_type = kwargs.get('function_type', 'linear')

    src_points_array = array(src_points)
    dest_points_array = array(dest_points)
    point_p_array = array(target_point)

    xa, ya, za = src_points_array.T
    xb, yb, zb = dest_points_array.T

    rbf_x = Rbf(xa, ya, za, xb, function=function_type)
    rbf_y = Rbf(xa, ya, za, yb, function=function_type)
    rbf_z = Rbf(xa, ya, za, zb, function=function_type)

    point_x = float(rbf_x(*point_p_array))
    point_y = float(rbf_y(*point_p_array))
    point_z = float(rbf_z(*point_p_array))

    logger.debug(f'Mapped point: {point_x}, {point_y}, {point_z}')

    return [point_x, point_y, point_z]
