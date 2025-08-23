"""Single command functions."""

from abc import ABC, abstractmethod

import maya.cmds as cmds


class BaseCommand(ABC):
    def validate_nodes(self, nodes: list[str]):
        """Validate the command.

        Args:
            nodes (list[str]): List of nodes to process.
        """
        if not nodes:
            raise ValueError("No nodes provided")

        not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
        if not_exists_nodes:
            raise ValueError(f"Node does not exist: {not_exists_nodes}")

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the command."""
        pass


class SceneCommand(BaseCommand):
    """Command to process the scene."""

    def __init__(self):
        """Initialize the command."""
        self.execute()

    def execute(self):
        """Execute the command."""
        pass


class AllCommand(BaseCommand):
    """Command to process all nodes."""

    def __init__(self, nodes: list[str]):
        """Initialize the command.

        Args:
            nodes (list[str]): The nodes to process.
        """
        self.validate_nodes(nodes)
        self.execute(nodes)

    def execute(self, nodes: list[str]):
        """Execute the command.

        Args:
            nodes (list[str]): The nodes to process.
        """
        pass


class PairCommand(BaseCommand):
    """Command to process a pair of nodes."""

    def __init__(self, source_nodes: list[str], target_nodes: list[str]):
        """Initialize the command.

        Notes:
            - Basically, source_nodes and target_nodes need to be the same number.
            - However, if there is only one source_node, it will be copied to match the number of target_nodes.

        Args:
            source_nodes (list[str]): List of source nodes to process.
            target_nodes (list[str]): List of target nodes to process.
        """
        if not source_nodes:
            raise ValueError("No source nodes provided")

        if not target_nodes:
            raise ValueError("No target nodes provided")

        nodes = source_nodes + target_nodes
        self.validate_nodes(nodes)

        if len(source_nodes) == 1:
            source_nodes = source_nodes * len(target_nodes)

        if len(source_nodes) != len(target_nodes):
            raise ValueError("Source and target nodes must be the same length")

        for source_node, target_node in zip(source_nodes, target_nodes, strict=False):
            self.execute(source_node, target_node)

    def execute(self, source_node: str, target_node: str):
        """Execute the command.

        Args:
            source_node (str): The source node to process.
            target_node (str): The target node to process.
        """
        pass
