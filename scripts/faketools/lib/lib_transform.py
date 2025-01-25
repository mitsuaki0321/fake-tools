"""
Transform functions.
"""

import math
from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds

logger = getLogger(__name__)


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


class TransformHierarchy:
    """Class to register and retrieve the hierarchy of transform nodes.

    Attributes:
        __hierarchy (dict): The hierarchy data.
        {
            'node_name': {
                'parent': str, # Parent node name.
                'children': list[str], # Children node names.
                'depth': int # Depth of the node.
                'register_parent': str, # Registered parent node name.
                'register_children': list[str], # Registered children node names.
            }
        }
    """

    def __init__(self):
        """Constructor.
        """
        self._hierarchy = {}

    @classmethod
    def set_hierarchy_data(cls, data: dict) -> 'TransformHierarchy':
        """Set the hierarchy data.

        Args:
            data (dict): The hierarchy data.

        Returns:
            HierarchyHandler: The hierarchy handler instance.
        """
        if not data:
            raise ValueError('Hierarchy data is not specified.')

        if not isinstance(data, dict):
            raise ValueError('Hierarchy data is not a dictionary.')

        # Validate the data
        for node, node_data in data.items():
            if not isinstance(node_data, dict):
                raise ValueError(f'Invalid node data: {node_data}')

            if 'parent' not in node_data:
                raise ValueError(f'Parent is not specified: {node_data}')

            if 'children' not in node_data:
                raise ValueError(f'Children is not specified: {node_data}')

            if 'depth' not in node_data:
                raise ValueError(f'Depth is not specified: {node_data}')

            if 'register_parent' not in node_data:
                raise ValueError(f'Register parent is not specified: {node_data}')

            if 'register_children' not in node_data:
                raise ValueError(f'Register children is not specified: {node_data}')

        instance = cls()
        instance._hierarchy = data

        return instance

    def get_hierarchy_data(self) -> dict:
        """Get the hierarchy data.

        Returns:
            dict: The hierarchy data.
        """
        return self._hierarchy

    def register_node(self, node: str) -> None:
        """Register the node to the hierarchy.

        Args:
            node (str): The target node.
        """
        if not node:
            raise ValueError('Node is not specified.')

        if not cmds.objExists(node):
            raise ValueError(f'Node does not exist: {node}')

        if 'transform' not in cmds.nodeType(node, inherited=True):
            raise ValueError(f'Node is not a transform: {node}')

        if node in self._hierarchy:
            cmds.warning(f'Node is already registered. Overwrite: {node}')

        parent_node = cmds.listRelatives(node, parent=True, path=True)
        child_nodes = cmds.listRelatives(node, children=True, path=True) or []

        full_path = cmds.ls(node, long=True)[0]
        depth = len(full_path.split('|')) - 1

        self._hierarchy[node] = {
            'parent': parent_node and parent_node[0] or None,
            'children': child_nodes,
            'register_parent': None,
            'register_children': [],
            'depth': depth
        }

        self.__update_register_hierarchy()

        logger.debug(f'Registered node: {node}')

    def __update_register_hierarchy(self) -> None:
        """Update the registered hierarchy in the data.

        Args:
            node (str): The target node.
        """
        # Clear the registered hierarchy
        for node in self._hierarchy:
            self._hierarchy[node]['register_parent'] = None
            self._hierarchy[node]['register_children'] = []

        # Update the registered hierarchy
        for node in self._hierarchy:
            parent = self._hierarchy[node]['parent']
            if not parent:
                continue

            full_path = cmds.ls(node, long=True)[0]
            parent_nodes = full_path.split('|')[1:-1]

            for parent_node in reversed(parent_nodes):
                if parent_node in self._hierarchy:
                    self._hierarchy[node]['register_parent'] = parent_node
                    self._hierarchy[parent_node]['register_children'].append(node)

                    logger.debug(f'Updated register hierarchy: {node} -> Parent: {parent_node}, Children: {node}')
                    break

    def get_parent(self, node: str) -> str:
        """Get the parent node of the node.

        Args:
            node (str): The target node.

        Returns:
            str: The parent node.
        """
        if not node:
            raise ValueError('Node is not specified.')

        if node not in self._hierarchy:
            raise ValueError(f'Node is not registered: {node}')

        return self._hierarchy[node]['parent']

    def get_children(self, node: str) -> list:
        """Get the children nodes of the node.

        Args:
            node (str): The target node.

        Returns:
            list: The children nodes.
        """
        if not node:
            raise ValueError('Node is not specified.')

        if node not in self._hierarchy:
            raise ValueError(f'Node is not registered: {node}')

        return self._hierarchy[node]['children']

    def get_registered_parent(self, node: str) -> str:
        """Get the registered parent node of the node.

        Args:
            node (str): The target node.

        Returns:
            str: The registered parent node.
        """
        if not node:
            raise ValueError('Node is not specified.')

        if node not in self._hierarchy:
            raise ValueError(f'Node is not registered: {node}')

        return self._hierarchy[node]['register_parent']

    def get_registered_children(self, node: str) -> list:
        """Get the registered children nodes of the node.

        Args:
            node (str): The target node.

        Returns:
            list: The registered children nodes.
        """
        if not node:
            raise ValueError('Node is not specified.')

        if node not in self._hierarchy:
            raise ValueError(f'Node is not registered: {node}')

        return self._hierarchy[node]['register_children']

    def __repr__(self):
        """Return the string representation of the hierarchy.
        """
        return f'{self.__class__.__name__}({self._hierarchy})'

    def __str__(self):
        """Return the string representation of the hierarchy.
        """
        return f'{self._hierarchy}'


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
