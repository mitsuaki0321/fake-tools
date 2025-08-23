"""
Duplicate and rename the node.
"""

from logging import getLogger

import maya.cmds as cmds

from ..lib import lib_api, lib_name

logger = getLogger(__name__)


def solve_rename(nodes: list[str], regex_name: str, *args, **kwargs) -> list[str]:
    """Solve the node name.

    Args:
        nodes (list[str]): The target node list.
        regex_name (str): The new name.

    Keyword Args:
        start_alphabet (int): The start alphabet. Default is 1.
        start_number (int): The start number. Default is 1.

    Notes:
        - If dagNode and nonDagNode are mixed, an error will be output.

    Returns:
        list[str]: The renamed node list.
    """
    logger.debug("Start")

    # Check node
    if not nodes:
        cmds.error("Nodes are not specified.")
    elif not isinstance(nodes, list):
        cmds.error("Nodes must be a list.")

    # Node exists
    not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
    if not_exists_nodes:
        cmds.error(f"Nodes do not exist: {not_exists_nodes}")

    dag_nodes = []
    non_dag_nodes = []
    for node in nodes:
        if cmds.objExists(node):
            if cmds.ls(node, dag=True):
                dag_nodes.append(node)
            else:
                non_dag_nodes.append(node)

    if dag_nodes and non_dag_nodes:
        cmds.error("DagNode and nonDagNode are mixed.")

    start_alpha = kwargs.get("start_alpha", "A")
    start_number = kwargs.get("start_number", 1)

    if dag_nodes:
        local_names = [node.split("|")[-1] for node in dag_nodes]
        new_names = lib_name.solve_names(local_names, regex_name, start_alpha=start_alpha, start_number=start_number)

        result_nodes = _rename_dag_nodes(dag_nodes, new_names)

        logger.debug("End dagNode")

        return result_nodes

    if non_dag_nodes:
        new_names = lib_name.solve_names(non_dag_nodes, regex_name, start_alpha=start_alpha, start_number=start_number)

        result_nodes = _rename_non_dag_nodes(non_dag_nodes, new_names)

        logger.debug("End nonDagNode")

        return result_nodes


def substitute_rename(nodes: list[str], regex_name: str, replace_name: str, *args, **kwargs) -> list[str]:
    """Substitute the node name.

    Args:
        nodes (list[str]): The target node list.
        regex_name (str): The name to substitute.
        replace_name (str): The new name.

    Returns:
        list[str]: The substituted node list.
    """
    logger.debug("Start")

    # Check node
    if not nodes:
        cmds.error("Nodes are not specified.")
    elif not isinstance(nodes, list):
        cmds.error("Nodes must be a list.")

    # Node exists
    not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
    if not_exists_nodes:
        cmds.error(f"Nodes do not exist: {not_exists_nodes}")

    dag_nodes = []
    non_dag_nodes = []
    for node in nodes:
        if cmds.objExists(node):
            if cmds.ls(node, dag=True):
                dag_nodes.append(node)
            else:
                non_dag_nodes.append(node)

    if dag_nodes and non_dag_nodes:
        cmds.error("DagNode and nonDagNode are mixed.")

    if dag_nodes:
        local_names = [node.split("|")[-1] for node in dag_nodes]
        new_names = lib_name.substitute_names(local_names, regex_name, replace_name)

        result_nodes = _rename_dag_nodes(dag_nodes, new_names)

        logger.debug("End dagNode")

        return result_nodes

    if non_dag_nodes:
        new_names = lib_name.substitute_names(non_dag_nodes, regex_name, replace_name)

        result_nodes = _rename_non_dag_nodes(non_dag_nodes, new_names)

        logger.debug("End nonDagNode")

        return result_nodes


def _rename_dag_nodes(nodes: list[str], new_names: list[str]) -> list[str]:
    """Rename the dag nodes.

    Args:
        nodes (list[str]): The target node list.
        new_names (list[str]): The new name list.

    Returns:
        list[str]: The renamed node list.
    """
    node_dag_paths = [lib_api.get_dag_path(node) for node in nodes]

    result_nodes = []
    for node_dag_path, new_name in zip(node_dag_paths, new_names, strict=False):
        node_name = node_dag_path.fullPathName()
        result_name = cmds.rename(node_name, new_name)

        result_nodes.append(result_name)

        local_node_name = node_name.split("|")[-1]
        local_new_name = result_name.split("|")[-1]
        if local_node_name == local_new_name:
            logger.debug(f"The name has not changed before and after: {local_node_name} -> {local_new_name}")
        else:
            logger.debug(f"Renamed: {local_node_name} -> {local_new_name}")

    return result_nodes


def _rename_non_dag_nodes(nodes: list[str], new_names: list[str]) -> list[str]:
    """Rename the non dag nodes.

    Args:
        nodes (list[str]): The target node list.
        new_names (list[str]): The new name list.

    Returns:
        list[str]: The renamed node list.
    """
    result_nodes = []
    for node, new_name in zip(nodes, new_names, strict=False):
        if node == new_name:
            result_nodes.append(node)
        else:
            new_name = cmds.rename(node, new_name)
            result_nodes.append(new_name)

        logger.debug(f"Renamed: {node} -> {new_name}")

    return result_nodes
