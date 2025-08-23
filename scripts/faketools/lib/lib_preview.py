"""
previewLocator node command.
"""

from logging import getLogger

import maya.cmds as cmds

logger = getLogger(__name__)


class PreviewLocator:
    """PreviewLocator class."""

    plugin_name = "previewLocator"
    node_name = "previewLocator"

    def __init__(self, node: str):
        """Initialize the PreviewLocatorCommand class.

        Args:
            node (str): previewLocator node name.
        """
        if not cmds.objExists(node):
            raise ValueError("Node does not exist.")

        if cmds.nodeType(node) != self.plugin_name:
            raise ValueError(f"Invalid node type: {cmds.nodeType(node)}")

        self._node = node
        self._shape_types = ["locator", "joint"]

    @classmethod
    def create(cls, name: str | None = None, recreate: bool = False):
        """Create a previewLocator node.

        Args:
            name (str, optional): The name of the previewLocator node.
            recreate (bool): Whether to recreate the node. Default is False.

        Returns:
            PreviewLocator: The previewLocator instance.
        """
        # Load the plugin if not loaded
        if not cmds.pluginInfo(cls.plugin_name, q=True, loaded=True):
            cmds.loadPlugin(cls.plugin_name)

        # Create the node
        if name and cmds.objExists(name):
            if recreate:
                if cmds.nodeType(name) == cls.plugin_name:
                    transform = cmds.listRelatives(name, parent=True)
                    cmds.delete(transform)
                else:
                    logger.warning(f"recreate flag is set but the node is not a previewLocator node: {name}")
                    raise ValueError(f"Node already exists: {name}")
            else:
                raise ValueError(f"Node already exists: {name}")

        if name is None:
            name = cls.node_name

        node = cmds.createNode(cls.node_name, name=name, ss=True)
        transform = cmds.listRelatives(node, parent=True)[0]
        cmds.rename(transform, f"{name}_transform")

        logger.debug(f"Created previewLocator node: {node}")

        return cls(node)

    @property
    def name(self) -> str:
        """Get the name of the previewLocator node.

        Returns:
            str: The name.
        """
        if not cmds.objExists(self._node):
            raise ValueError("Node does not exist.")

        return self._node

    @property
    def transform_name(self) -> str:
        """Get the transform name of the previewLocator node.

        Returns:
            str: The transform name.
        """
        if not cmds.objExists(self._node):
            raise ValueError("Node does not exist.")

        return cmds.listRelatives(self._node, parent=True)[0]

    @property
    def shape_type(self) -> str:
        """Get the shape type of the previewLocator node.

        Returns:
            str: The shape type.
        """
        return self._shape_types[cmds.getAttr(f"{self._node}.shapeType")]

    @shape_type.setter
    def shape_type(self, value: str):
        """Set the shape type of the previewLocator node.

        Args:
            value (str): The shape type.
        """
        if value not in self._shape_types:
            raise ValueError(f"Invalid shape type: {value}")

        cmds.setAttr(f"{self._node}.shapeType", self._shape_types.index(value))

    @property
    def global_size(self) -> float:
        """Get the global size of the previewLocator node.

        Returns:
            float: The global size.
        """
        return cmds.getAttr(f"{self._node}.shapeGlobalSize")

    @global_size.setter
    def global_size(self, value: float):
        """Set the global size of the previewLocator node.

        Args:
            value (float): The global size.
        """
        cmds.setAttr(f"{self._node}.shapeGlobalSize", value)

    @property
    def line_width(self) -> float:
        """Get the line width of the previewLocator node.

        Returns:
            float: The line width.
        """
        return cmds.getAttr(f"{self._node}.lineWidth")

    @line_width.setter
    def line_width(self, value: float):
        """Set the line width of the previewLocator node.

        Args:
            value (float): The line width.
        """
        cmds.setAttr(f"{self._node}.lineWidth", value)

    @property
    def manipulation_color(self) -> bool:
        """Get the manipulation color settings of the previewLocator node.

        Returns:
            bool: The manipulation color.
        """
        return cmds.getAttr(f"{self._node}.manipulationColor")

    @manipulation_color.setter
    def manipulation_color(self, value: bool):
        """Set the manipulation color settings of the previewLocator node.

        Args:
            value (bool): The manipulation color.
        """
        cmds.setAttr(f"{self._node}.manipulationColor", value)

    @property
    def num_shapes(self) -> int:
        """Get the number of shapes of the previewLocator node.

        Returns:
            int: The number of shapes.
        """
        return cmds.getAttr(f"{self._node}.shape", size=True)

    def get_shape_color(self, index: int) -> list[float]:
        """Get the shape color of the index data.

        Args:
            index (int): The shape index.

        Returns:
            list[float]: The shape color.
        """
        if index >= self.num_shapes:
            raise ValueError(f"Invalid shape index: {index}")

        return cmds.getAttr(f"{self._node}.shape[{index}].shapeColor")[0]

    def set_shape_color(self, index: int, color: list[float]):
        """Set the shape color of the index data.

        Args:
            index (int): The shape index.
            color (list[float]): The shape color.
        """
        cmds.setAttr(f"{self._node}.shape[{index}].shapeColor", *color)

    def get_shape_hierarchy(self, index: int) -> bool:
        """Get the shape hierarchy settings of the index data.

        Args:
            index (int): The shape index.

        Returns:
            bool: The shape hierarchy settings.
        """
        if index >= self.num_shapes:
            raise ValueError(f"Invalid shape index: {index}")

        return cmds.getAttr(f"{self._node}.shape[{index}].shapeHierarchy")

    def set_shape_hierarchy(self, index: int, value: bool):
        """Set the shape hierarchy settings of the index data.

        Args:
            index (int): The shape index.
            value (bool): The shape hierarchy settings.
        """
        cmds.setAttr(f"{self._node}.shape[{index}].shapeHierarchy", value)

    def get_shape_sizes(self, index: int) -> list[float]:
        """Get the shape sizes of the index data.

        Args:
            index (int): The shape index.

        Returns:
            list[float]: The shape sizes.
        """
        if index >= self.num_shapes:
            raise ValueError(f"Invalid shape index: {index}")

        num_transforms = cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform", size=True)
        if num_transforms == 0:
            return None

        sizes = []
        for i in range(num_transforms):
            sizes.append(cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapeSize"))

        return sizes

    def set_shape_sizes(self, index: int, sizes: list[float]):
        """Set the shape sizes of the index data.

        Args:
            index (int): The shape index.
            sizes (list[float]): The shape sizes.
        """
        num_items = len(sizes)
        for i in range(num_items):
            cmds.setAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapeSize", sizes[i])

    def get_shape_positions(self, index: int) -> list[list[float]]:
        """Get the shape positions of the index data.

        Args:
            index (int): The shape index.

        Returns:
            list[list[float]]: The shape positions.
        """
        if index >= self.num_shapes:
            raise ValueError(f"Invalid shape index: {index}")

        num_transforms = cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform", size=True)
        if num_transforms == 0:
            return None

        positions = []
        for i in range(num_transforms):
            positions.append(cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapePosition")[0])

        return positions

    def set_shape_positions(self, index: int, positions: list[list[float]]):
        """Set the shape positions of the index data.

        Args:
            index (int): The shape index.
            positions (list[list[float]]): The shape positions.
        """
        num_items = len(positions)
        for i in range(num_items):
            cmds.setAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapePosition", *positions[i])

    def get_shape_rotations(self, index: int) -> list[list[float]]:
        """Get the shape rotations of the index data.

        Args:
            index (int): The shape index.

        Returns:
            list[list[float]]: The shape rotations.
        """
        if index >= self.num_shapes:
            raise ValueError(f"Invalid shape index: {index}")

        num_transforms = cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform", size=True)
        if num_transforms == 0:
            return None

        rotations = []
        for i in range(num_transforms):
            rotations.append(cmds.getAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapeRotation")[0])

        return rotations

    def set_shape_rotations(self, index: int, rotations: list[list[float]]):
        """Set the shape rotations of the index data.

        Args:
            index (int): The shape index.
            rotations (list[list[float]]): The shape rotations.
        """
        num_items = len(rotations)
        for i in range(num_items):
            cmds.setAttr(f"{self._node}.shape[{index}].shapeTransform[{i}].shapeRotation", *rotations[i])

    def clear_shapes(self):
        """Clear all shape data."""
        if self.num_shapes == 0:
            return

        for i in range(self.num_shapes):
            cmds.removeMultiInstance(f"{self._node}.shape[{i}]", b=True)

    def __repr__(self):
        """Representation of the PreviewLocator instance."""
        return f"{self.__class__.__name__}({self._node})"

    def __str__(self):
        """String representation of the PreviewLocator instance."""
        return self._node
