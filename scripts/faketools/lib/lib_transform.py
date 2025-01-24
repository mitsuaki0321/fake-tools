"""
Transform functions.
"""

import math
from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds

logger = getLogger(__name__)


def mirror_transform(source_node: str, target_node: str, axis: str = 'x', mirror_position: bool = True, mirror_rotation: bool = True) -> None:
    """Mirror the transform.

    Args:
        source_node (str): The source node.
        target_node (str): The target node.
        axis (str): The axis to mirror. Default is 'x'.
        mirror_position (bool): Whether to mirror position. Default is True.
        mirror_rotation (bool): Whether to mirror rotation. Default is True.
    """
    if not source_node or not target_node:
        raise ValueError('Node is not specified.')

    # Check the node
    if not cmds.objExists(source_node) or not cmds.objExists(target_node):
        cmds.error(f'Node does not exist: {source_node} or {target_node}')

    if axis not in ['x', 'y', 'z']:
        raise ValueError(f'Invalid axis: {axis}')

    if not mirror_position and not mirror_rotation:
        raise ValueError('Position and rotation are both False')

    # Mirror the transform
    world_matrix = cmds.getAttr(f'{source_node}.worldMatrix')
    world_matrix = om.MMatrix(world_matrix)

    if axis == 'x':
        mirror_matrix = om.MMatrix(
            [
                [-1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ]
        )
    elif axis == 'y':
        mirror_matrix = om.MMatrix(
            [
                [1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ]
        )
    else:
        mirror_matrix = om.MMatrix(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ]
        )

    new_matrix = world_matrix * mirror_matrix
    transform_mat = om.MTransformationMatrix(new_matrix)
    position = transform_mat.translation(om.MSpace.kWorld)
    rotation = transform_mat.rotation()
    rotation = [math.degrees(angle) for angle in [rotation.x, rotation.y, rotation.z]]
    scale = transform_mat.scale(om.MSpace.kWorld)

    if mirror_position:
        cmds.xform(target_node, translation=position, worldSpace=True)
        logger.debug(f'Mirrored position: {source_node} -> {target_node}')

    if mirror_rotation:
        cmds.xform(target_node, rotation=rotation, scale=scale, worldSpace=True)
        logger.debug(f'Mirrored rotation: {source_node} -> {target_node}')


class FreezeTransformNode:

    def __init__(self, node: str):
        """Initialize the FreezeTransformNode with a target transform node.

        Args:
            node (str): The target transform node.

        Raises:
            ValueError: If the node does not exist, is not a transform node, or is not a string.
        """
        if not node or not isinstance(node, str):
            raise ValueError('Node is not specified or not a string.')

        if not cmds.objExists(node):
            raise ValueError(f'Node does not exist: {node}')

        if 'transform' not in cmds.nodeType(node, inherited=True):
            raise ValueError(f'Node is not a transform: {node}')

        self.node = node

    def _unlock_and_lock(func):
        """Decorator to unlock and lock the locked attributes.
        """

        def wrapper(self, *args, **kwargs):
            """
            """
            # Check isConnected
            connected_state = False
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                if cmds.connectionInfo(f'{self.node}.{attr}', isDestination=True):
                    logger.debug(f'Connected attribute: {self.node}.{attr}')
                    connected_state = True
                    return

            if connected_state:
                cmds.error(f'Failed to freeze transform because connections exist: {self.node}')

            # Check locked attributes
            locked_attrs = cmds.listAttr(self.node, locked=True) or []

            for attr in locked_attrs:
                cmds.setAttr(f'{self.node}.{attr}', lock=False)
            try:
                func(self, *args, **kwargs)
            finally:
                for attr in locked_attrs:
                    cmds.setAttr(f'{self.node}.{attr}', lock=True)

        return wrapper

    @_unlock_and_lock
    def freeze_transform(self) -> None:
        """Freeze the transform of the nodes.

        Notes:
            - Even if the transform attributes of the children are locked, they will be forcibly unlocked and processed.
        """
        nodes = cmds.listRelatives(self.node, ad=True, path=True, type='transform') or []
        nodes.append(self.node)

        # Unlock the locked attributes
        locked_data = {}
        for node in nodes:
            attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'jox', 'joy', 'joz']
            locked_attrs = []
            for attr in attrs:
                if cmds.nodeType(node) == 'joint':
                    if cmds.getAttr(f'{node}.{attr}', lock=True):
                        locked_attrs.append(attr)
                        cmds.setAttr(f'{node}.{attr}', lock=False)
                else:
                    if attr in ['jox', 'joy', 'joz']:
                        continue
                    if cmds.getAttr(f'{node}.{attr}', lock=True):
                        locked_attrs.append(attr)
                        cmds.setAttr(f'{node}.{attr}', lock=False)

            if locked_attrs:
                locked_data[node] = locked_attrs
                logger.debug(f'Unlocked attributes: {node} -> {locked_attrs}')

        # Freeze the transform
        cmds.makeIdentity(self.node, apply=True, t=True, r=True, s=True, n=0, pn=True)
        logger.debug(f'Freeze transform: {self.node}')

        # Lock the locked attributes
        for node, attrs in locked_data.items():
            for attr in attrs:
                cmds.setAttr(f'{node}.{attr}', lock=True)

    @_unlock_and_lock
    def freeze_pivot(self) -> None:
        """Freeze the pivot of the node.
        """
        cmds.makeIdentity(self.node, apply=False, t=True, r=True, s=True, n=0, pn=True)
        logger.debug(f'Freeze pivot: {self.node}')

    def freeze_vertex(self) -> None:
        """Freeze the vertex of the node.
        """
        shape = cmds.listRelatives(self.node, ad=True, path=True, type='mesh')
        if not shape:
            cmds.warning(f'No mesh found: {self.node}')
            return

        cmds.cluster(self.node)
        cmds.delete(self.node, ch=True)

        logger.debug(f'Freeze vertex: {self.node}')

    def freeze(self, freeze_transform: bool = True, freeze_pivot: bool = True, freeze_vertex: bool = True) -> None:
        """Freeze the node with specified options.

        Args:
            freeze_transform (bool, optional): If True, freeze the transform. Defaults to False.
            freeze_pivot (bool, optional): If True, freeze the pivot. Defaults to False.
            freeze_vertex (bool, optional): If True, freeze the vertex. Defaults to False.
        """
        if freeze_transform:
            self.freeze_transform()
        if freeze_pivot:
            self.freeze_pivot()
        if freeze_vertex:
            self.freeze_vertex()


def reorder_transform_nodes(nodes: list[str]) -> list:
    """Reorder transform nodes by hierarchy depth.

    Args:
        nodes (list[str]): List of transform nodes.

    Returns:
        list: Reordered list of transform nodes.
    """
    if not nodes:
        raise ValueError('Nodes are not specified.')

    not_transform_nodes = [node for node in nodes if 'transform' not in cmds.nodeType(node, inherited=True)]
    if not_transform_nodes:
        raise ValueError(f'Nodes are not transform nodes: {not_transform_nodes}')

    depth_dict = {}
    for node in nodes:
        depth = len(cmds.ls(node, long=True)[0].split('|')) - 1
        depth_dict[node] = depth

    sorted_nodes = sorted(nodes, key=lambda x: depth_dict[x])

    return sorted_nodes


def is_unique_node(node: str) -> bool:
    """Check if the node is unique name node.

    Args:
        node (str): The target node.

    Returns:
        bool: Whether the node is unique.
    """
    if not node:
        raise ValueError('Node is not specified.')

    node = cmds.ls(node)
    if '|' in node:
        return False

    return True
