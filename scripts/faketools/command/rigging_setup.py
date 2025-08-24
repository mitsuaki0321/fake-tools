"""
Rigging setup command.
"""

from logging import getLogger
import math

import maya.api.OpenMaya as om
import maya.cmds as cmds

from ..lib import lib_attribute

logger = getLogger(__name__)


def combine_rotation(node: str, target_attribute: str = "rotate") -> None:
    """Combines the rotation of the node.

    Args:
        node (str): The target node.
        target_attribute (str): The target attribute. Default is 'rotate'. 'rotate' or 'rotateAxis' or 'jointOrient'.
    """
    if not node:
        raise ValueError("Node is not specified.")

    if not cmds.objExists(node):
        raise ValueError(f"Node does not exist: {node}")

    if cmds.nodeType(node) == "joint":
        raise ValueError(f"Node is a joint: {node}")

    target_attributes = ["rotate", "rotateAxis", "jointOrient"]
    if target_attribute not in target_attributes:
        raise ValueError(f"Invalid target attribute: {target_attribute}")

    lock_attrs = []
    for attr in target_attributes:
        attrs = cmds.attributeQuery(attr, node=node, listChildren=True)
        attrs.insert(0, attr)
        for attr in attrs:
            if cmds.getAttr(f"{node}.{attr}", lock=True):
                cmds.setAttr(f"{node}.{attr}", lock=False)
                lock_attrs.append(attr)

    rotate_axis = cmds.getAttr(f"{node}.rotateAxis")[0]
    rotate = cmds.getAttr(f"{node}.rotate")[0]
    joint_orient = cmds.getAttr(f"{node}.jointOrient")[0]

    if target_attribute == "rotate":
        if rotate_axis == [0, 0, 0] and joint_orient == [0, 0, 0]:
            return
    elif target_attribute == "rotateAxis":
        if rotate == [0, 0, 0] and joint_orient == [0, 0, 0]:
            return
    elif target_attribute == "jointOrient" and rotate == [0, 0, 0] and rotate_axis == [0, 0, 0]:
        return

    rotate_order = cmds.getAttr(f"{node}.rotateOrder")
    rotate_axis_quat = om.MEulerRotation(
        math.radians(rotate_axis[0]), math.radians(rotate_axis[1]), math.radians(rotate_axis[2]), rotate_order
    ).asQuaternion()

    rotate_quat = om.MEulerRotation(math.radians(rotate[0]), math.radians(rotate[1]), math.radians(rotate[2]), rotate_order).asQuaternion()

    joint_orient_quat = om.MEulerRotation(
        math.radians(joint_orient[0]), math.radians(joint_orient[1]), math.radians(joint_orient[2]), rotate_order
    ).asQuaternion()

    combine_quat = rotate_axis_quat * rotate_quat * joint_orient_quat
    combine_euler = combine_quat.asEulerRotation()

    combine_rotation = [math.degrees(combine_euler.x), math.degrees(combine_euler.y), math.degrees(combine_euler.z)]

    cmds.setAttr(f"{node}.{target_attribute}", *combine_rotation)

    if lock_attrs:
        for attr in lock_attrs:
            cmds.setAttr(f"{node}.{attr}", lock=True)

    logger.debug(f"Combined rotation for {node} with target attribute: {target_attribute}")


def zero_out_attributes(node: str, attributes: list) -> None:
    """Zeroes out the attributes of the node.

    Args:
        node (str): The target node.
        attributes (list): The target attributes.
    """
    if not node:
        raise ValueError("Node is not specified.")

    if not cmds.objExists(node):
        raise ValueError(f"Node does not exist: {node}")

    if not attributes:
        raise ValueError("Attributes are not specified.")

    not_exist_attrs = [attr for attr in attributes if not cmds.attributeQuery(attr, node=node, exists=True)]
    if not_exist_attrs:
        raise ValueError(f"Attributes do not exist: {not_exist_attrs}")

    lock_handler = lib_attribute.AttributeLockHandler()
    lock_handler.stock_lock_attrs(node, attributes, include_parent=True)

    for attr in attributes:
        if not lib_attribute.is_modifiable(node, attr):
            cmds.warning(f"Skip zero out: Attribute is not modifiable: {node}.{attr}")
            continue

        default_value = cmds.attributeQuery(attr, node=node, listDefault=True)[0]
        cmds.setAttr(f"{node}.{attr}", default_value)

        logger.debug(f"Zeroed out attribute: {node}.{attr} -> {default_value}")

    lock_handler.restore_lock_attrs(node)


def mirror_dag_node(source_node: str, target_node: str, axis: str = "x", mirror_position: bool = True, mirror_rotation: bool = True) -> None:
    """Mirror the dag node.

    Args:
        source_node (str): The source node.
        target_node (str): The target node.
        axis (str): The axis to mirror. Default is 'x'.
        mirror_position (bool): Whether to mirror position. Default is True.
        mirror_rotation (bool): Whether to mirror rotation. Default is True.
    """
    if not source_node or not target_node:
        raise ValueError("Node is not specified.")

    # Check the node
    if not cmds.objExists(source_node) or not cmds.objExists(target_node):
        cmds.error(f"Node does not exist: {source_node} or {target_node}")

    if axis not in ["x", "y", "z"]:
        raise ValueError(f"Invalid axis: {axis}")

    if not mirror_position and not mirror_rotation:
        raise ValueError("Position and rotation are both False")

    # Check target node attributes
    transform_attribute = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]
    lock_handler = lib_attribute.AttributeLockHandler()
    lock_handler.stock_lock_attrs(target_node, transform_attribute, include_parent=True)
    not_modifiable_attrs = [attr for attr in transform_attribute if not lib_attribute.is_modifiable(target_node, attr)]
    if not_modifiable_attrs:
        raise ValueError(f"Target node attributes are not modifiable: {target_node} -> {not_modifiable_attrs}")

    # Mirror the transform
    world_matrix = cmds.getAttr(f"{source_node}.worldMatrix")
    world_matrix = om.MMatrix(world_matrix)

    if axis == "x":
        mirror_matrix = om.MMatrix([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    elif axis == "y":
        mirror_matrix = om.MMatrix([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    else:
        mirror_matrix = om.MMatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

    new_matrix = world_matrix * mirror_matrix
    transform_mat = om.MTransformationMatrix(new_matrix)
    position = transform_mat.translation(om.MSpace.kWorld)
    rotation = transform_mat.rotation()
    rotation = [math.degrees(angle) for angle in [rotation.x, rotation.y, rotation.z]]
    scale = transform_mat.scale(om.MSpace.kWorld)

    if mirror_position:
        cmds.xform(target_node, translation=position, worldSpace=True)
        logger.debug(f"Mirrored position: {source_node} -> {target_node}")

    if mirror_rotation:
        cmds.xform(target_node, rotation=rotation, scale=scale, worldSpace=True)
        logger.debug(f"Mirrored rotation: {source_node} -> {target_node}")

    lock_handler.restore_lock_attrs(target_node)
