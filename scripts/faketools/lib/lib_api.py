"""
Maya API functions
"""

import maya.api.OpenMaya as om


def get_dag_path(node: str) -> om.MDagPath:
    """Converts the node to the MDagPath.

    Args:
        node (str): The node.

    Returns:
        MDagPath: The MDagPath.
    """
    selection_list = om.MSelectionList()
    selection_list.add(node)
    dag_path = selection_list.getDagPath(0)

    return dag_path


def get_depend_node(node: str) -> om.MObject:
    """Converts the node to the MObject.

    Args:
        node (str): The node.

    Returns:
        MObject: The MObject.
    """
    selection_list = om.MSelectionList()
    selection_list.add(node)
    depend_node = selection_list.getDependNode(0)

    return depend_node
