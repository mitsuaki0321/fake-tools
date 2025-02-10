"""
Duplicate and rename the node.
"""

from logging import getLogger

import maya.cmds as cmds

from ..lib import lib_name, lib_selection, lib_shape
from . import rename_node

logger = getLogger(__name__)


def substitute_duplicate(nodes: list[str], regex_name: str, replace_name: str, *args, **kwargs) -> list[str]:
    """Substitute the duplicate node name.

    Args:
        nodes (list[str]): The target node list.
        regex_name (str): The name to substitute.
        replace_name (str): The new name.

    Returns:
        list[str]: The substituted node list.
    """
    # Check node
    if not nodes:
        cmds.error('Nodes are not specified.')
    elif not isinstance(nodes, list):
        cmds.error('Nodes must be a list.')

    # Node exists
    not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
    if not_exists_nodes:
        cmds.error(f'Nodes do not exist: {not_exists_nodes}')

    dag_nodes = []
    non_dag_nodes = []
    for node in nodes:
        if cmds.objExists(node):
            if cmds.ls(node, dag=True):
                dag_nodes.append(node)
            else:
                non_dag_nodes.append(node)

    if dag_nodes and non_dag_nodes:
        cmds.error('DagNode and nonDagNode are mixed.')

    if dag_nodes:
        transform_nodes = []
        for node in dag_nodes:
            if 'transform' in cmds.nodeType(node, inherited=True):
                transform_nodes.append(node)
            elif 'shape' in cmds.nodeType(node, inherited=True):
                transform_node = cmds.listRelatives(node, parent=True, f=True)[0]
                transform_nodes.append(transform_node)

        # Get only the top of the hierarchy for nodes with duplicate hierarchy
        transform_nodes = lib_selection.DagHierarchy(transform_nodes).get_hierarchy_tops()

        logger.debug(f'Before rename nodes: {transform_nodes}')

        result_nodes = []
        for transform_node in transform_nodes:
            dup_nodes = cmds.duplicate(transform_node, rc=True)

            hierarchy_nodes = lib_selection.DagHierarchy([transform_node]).get_hierarchy()
            local_names = [lib_name.get_local_name(node) for node in hierarchy_nodes]
            new_names = lib_name.substitute_names(local_names, regex_name, replace_name)

            rename_nodes = rename_node._rename_dag_nodes(dup_nodes, new_names)

            result_nodes.extend(rename_nodes)

        return result_nodes

    if non_dag_nodes:
        logger.debug(f'Before rename nodes: {non_dag_nodes}')

        new_names = lib_name.substitute_names(non_dag_nodes, regex_name, replace_name)
        dup_nodes = cmds.duplicate(non_dag_nodes, rc=True)
        result_nodes = rename_node._rename_non_dag_nodes(dup_nodes, new_names)

        return result_nodes


def substitute_duplicate_original(nodes: list[str], regex_name: str, replace_name: str, *args, **kwargs) -> list[str]:
    """Duplicate the original shape of the shape node and replace it with the specified name.

    Args:
        nodes (list[str]): The target node list.
        regex_name (str): The name to substitute.
        replace_name (str): The new name.

    Notes:
        - Target node type is shape node. Only mesh, nurbsSurface, nurbsCurve.

    Returns:
        list[str]: The substituted node list.
    """
    logger.debug('Start')

    # Check node
    if not nodes:
        cmds.error('Nodes are not specified.')
    elif not isinstance(nodes, list):
        cmds.error('Nodes must be a list.')

    # Node exists
    not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
    if not_exists_nodes:
        cmds.error(f'Nodes do not exist: {not_exists_nodes}')

    # Duplicate original shape
    dup_nodes = []
    name_nodes = []
    for node in nodes:
        shp = cmds.listRelatives(node, shapes=True, f=True)
        if not shp:
            cmds.warning(f'Node has no shape: {node}')
            continue

        if cmds.nodeType(shp[0]) not in ['mesh', 'nurbsSurface', 'nurbsCurve']:
            cmds.warning(f'Node is not a shape: {node}')
            continue

        orig_transform = lib_shape.duplicate_original_shape(shp[0])
        dup_nodes.append(orig_transform)
        name_nodes.append(node)

    if not dup_nodes:
        cmds.warning('No original shape duplicated.')
        return []

    # Substitute name
    new_names = lib_name.substitute_names(name_nodes, regex_name, replace_name)
    result_nodes = rename_node._rename_non_dag_nodes(dup_nodes, new_names)

    logger.debug('End')

    return result_nodes
