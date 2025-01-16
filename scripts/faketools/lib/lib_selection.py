"""
Node selection functions.
"""

import re
from logging import getLogger
from typing import Optional

import maya.cmds as cmds

logger = getLogger(__name__)


class NodeFilter:
    """Node selection by filter.
    """

    def __init__(self, nodes: list[str]):
        """Constructor.

        Args:
            nodes (list[str]): The node list.
        """
        if not nodes:
            raise ValueError('Nodes are not specified.')
        elif not isinstance(nodes, list):
            raise ValueError('Nodes must be a list.')

        not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
        if not_exists_nodes:
            raise ValueError(f'Nodes do not exist: {not_exists_nodes}')

        self.nodes = nodes

    def by_type(self, node_type: str, *args, **kwargs) -> list[str]:
        """Filters the nodes by the type.

        Args:
            node_type (str): The node type.

        Keyword Args:
            invert_match (bool): Whether to invert the match. Default is False.

        Returns:
            list: The filtered nodes.
        """
        invert_match = kwargs.get('invert_match', False)

        nodes = []
        for node in self.nodes:
            node_types = cmds.nodeType(node, inherited=True)
            if invert_match:
                if node_type not in node_types:
                    nodes.append(node)
            else:
                if node_type in node_types:
                    nodes.append(node)

        return nodes

    def by_regex(self, regex: str, *args, **kwargs) -> list[str]:
        """Filters the nodes by the regex.

        Args:
            regex (str): The regex.

        Keyword Args:
            invert_match (bool): Whether to invert the match. Default is False.

        Returns:
            list: The filtered nodes.
        """
        invert_match = kwargs.get('invert_match', False)
        ignorecase = kwargs.get('ignorecase', False)

        p = re.compile(regex, re.IGNORECASE) if ignorecase else re.compile(regex)

        nodes = []
        for node in self.nodes:
            if invert_match:
                if not p.match(node):
                    nodes.append(node)
            else:
                if p.match(node):
                    nodes.append(node)

        return nodes


class DagHierarchy:
    """Get the hierarchy nodes for dagNodes.
    """

    def __init__(self, nodes: list[str]):
        """Constructor.

        Args:
            nodes (list[str]): The node list.
        """
        if not nodes:
            raise ValueError('Nodes are not specified.')
        elif not isinstance(nodes, list):
            raise ValueError('Nodes must be a list.')

        not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
        if not_exists_nodes:
            cmds.error(f'Nodes do not exist: {not_exists_nodes}')

        not_dag_nodes = [node for node in nodes if 'dagNode' not in cmds.nodeType(node, inherited=True)]
        if not_dag_nodes:
            cmds.error(f'Nodes are not dagNode: {not_dag_nodes}')

        self.nodes = nodes

    def get_parent(self) -> list[str]:
        """Get the parent nodes.

        Notes:
            - Only transform node is supported.

        Returns:
            list[str]: The parent nodes.
        """
        result_nodes = []
        for node in self.nodes:
            parent = cmds.listRelatives(node, parent=True, path=True)
            if parent:
                if parent[0] not in result_nodes:
                    result_nodes.append(parent[0])

        return result_nodes

    def get_children(self, include_shape: bool = False) -> list[str]:
        """Get the children nodes.

        Args:
            include_shape (bool): Whether to include shapes. Default is False.

        Returns:
            list[str]: The children nodes.
        """
        result_nodes = []
        for node in self.nodes:
            if include_shape:
                children = cmds.listRelatives(node, children=True, path=True)
            else:
                children = cmds.listRelatives(node, children=True, path=True, type='transform')

            if children:
                for child in children:
                    if child not in result_nodes:
                        result_nodes.append(child)

        return result_nodes

    def get_siblings(self) -> list[str]:
        """Get the sibling transform nodes.

        Returns:
            list[str]: The sibling nodes.
        """
        result_nodes = []
        for node in self.nodes:
            if 'transform' not in cmds.nodeType(node, inherited=True):
                continue

            parent = cmds.listRelatives(node, parent=True, path=True)
            if parent:
                children = cmds.listRelatives(parent[0], children=True, path=True, type='transform')
                if children:
                    for child in children:
                        if child not in result_nodes:
                            result_nodes.append(child)
            else:
                world_nodes = cmds.ls(assemblies=True, long=True)
                for world_node in world_nodes:
                    if world_node in ['|persp', '|top', '|front', '|side']:
                        continue

                    if world_node not in result_nodes:
                        result_nodes.append(world_node)

        return result_nodes

    def get_shapes(self, shape_type: Optional[str] = None) -> list[str]:
        """Get the shapes.

        Args:
            shape_type (Optional[str]): The shape type.If None, all shapes are returned.

        Notes:
            - Only transform nodes are supported.

        Returns:
            list[str]: The shapes.
        """
        shapes = self.get_children(include_shape=True)
        if not shapes:
            return []

        if shape_type:
            return cmds.ls(shapes, type=shape_type, long=True)
        else:
            return shapes

    def get_hierarchy(self, include_shape: bool = False) -> list[str]:
        """Get the hierarchy nodes.

        Args:
            include_shape (bool): Whether to include shapes. Default is False.

        Returns:
            list[str]: The children nodes.
        """
        result_nodes = []

        def __get_children_recursive(node: str):
            """Get the children nodes recursively.
            """
            if node not in result_nodes:
                result_nodes.append(node)

            if 'transform' not in cmds.nodeType(node, inherited=True):
                return

            if include_shape:
                children = cmds.listRelatives(node, children=True, path=True)
            else:
                children = cmds.listRelatives(node, children=True, path=True, type='transform')

            if children:
                for child in children:
                    __get_children_recursive(child)

        for node in self.nodes:
            __get_children_recursive(node)

        return result_nodes

    def get_children_bottoms(self) -> list[str]:
        """Get the hierarchy bottom nodes.

        Returns:
            list[str]: The leaf nodes.
        """
        nodes = self.get_hierarchy(include_shape=False)

        result_nodes = []
        for node in nodes:
            children = cmds.listRelatives(node, children=True, path=True, type='transform')
            if not children:
                result_nodes.append(node)

        return result_nodes

    def get_hierarchy_tops(self) -> list[str]:
        """Get the hierarchy top nodes.

        Notes:
            - Retrieves only the top nodes among the selected nodes. For example, if joint1|joint2|joint3 is selected, joint1 is retrieved.

        Returns:
            list[str]: The top nodes.
        """
        nodes = cmds.ls(self.nodes, l=True)
        nodes = sorted(nodes, key=lambda x: x.count('|'), reverse=True)

        except_nodes = []
        for node in nodes:
            for comp_node in nodes:
                if node == comp_node:
                    continue

                if node.startswith(comp_node):
                    except_nodes.append(node)
                    break

        return cmds.ls([node for node in nodes if node not in except_nodes])
