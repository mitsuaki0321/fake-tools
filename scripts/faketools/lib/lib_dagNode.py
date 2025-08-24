"""
DagNode functions.
"""

from logging import getLogger

import maya.cmds as cmds

logger = getLogger(__name__)


class CleanUpNode:
    """Clean up the dagNode."""

    def __init__(self, node: str):
        """Initialize the NodeCleaner with a target node.

        Args:
            node (str): The target dagNode.

        Raises:
            ValueError: If the node does not exist or is not a transform node.
        """
        if not node:
            raise ValueError("Node is not specified.")

        if not isinstance(node, str):
            raise ValueError("Node must be a string.")

        if not cmds.objExists(node):
            raise ValueError(f"Node does not exist: {node}")

        if "dagNode" not in cmds.nodeType(node, inherited=True):
            raise ValueError(f"Node is not a dagNode: {node}")

        self.node = node

    def unlock_attributes(self) -> None:
        """Unlock all locked attributes of the node."""
        lock_attrs = cmds.listAttr(self.node, locked=True)
        if lock_attrs:
            for attr in lock_attrs:
                cmds.setAttr(f"{self.node}.{attr}", lock=False)
                logger.debug(f"Unlocked attribute: {self.node}.{attr}")

    def delete_user_attributes(self) -> None:
        """Delete all user-defined attributes of the node."""
        user_attrs = cmds.listAttr(self.node, userDefined=True)
        if user_attrs:
            for attr in user_attrs:
                cmds.deleteAttr(f"{self.node}.{attr}")
                logger.debug(f"Deleted user attribute: {self.node}.{attr}")

    def remove_from_sets(self) -> None:
        """Remove the node from all sets."""
        object_sets = cmds.listSets(object=self.node)
        if object_sets:
            for obj_set in object_sets:
                cmds.sets(self.node, remove=obj_set)
                logger.debug(f"Removed from set: {obj_set} << {self.node}")

    def apply_initial_shader(self) -> None:
        """Apply the initial shader to the node's shape."""
        if "shape" not in cmds.nodeType(self.node, inherited=True):
            shape = cmds.listRelatives(self.node, shapes=True, path=True)
            if not shape:
                cmds.warning(f"No shape found: {self.node}")
                return
            self.node = shape[0]

        shape_type = cmds.nodeType(self.node)
        if shape_type not in ["mesh", "nurbsSurface"]:
            cmds.warning(f"Unsupported shape type: {shape_type}")
            return

        cmds.sets(self.node, edit=True, forceElement="initialShadingGroup")
        logger.debug(f"Applied initial shader: {self.node}")

    def reset_override_enabled(self) -> None:
        """Reset the overrideEnabled attribute of the node."""
        override_enabled = cmds.getAttr(f"{self.node}.overrideEnabled")
        if override_enabled:
            cmds.setAttr(f"{self.node}.overrideEnabled", 0)
            cmds.setAttr(f"{self.node}.overrideDisplayType", 0)
            cmds.setAttr(f"{self.node}.overrideLevelOfDetail", 0)
            cmds.setAttr(f"{self.node}.overrideShading", 1)
            cmds.setAttr(f"{self.node}.overrideTexturing", 1)
            cmds.setAttr(f"{self.node}.overridePlayback, 1")
            cmds.setAttr(f"{self.node}.overrideVisibility", 1)
            cmds.setAttr(f"{self.node}.overrideColor", 0)
            cmds.setAttr(f"{self.node}.overrideColorRGB", 0, 0, 0)
            cmds.setAttr(f"{self.node}.overrideColorA", 1)

            logger.debug(f"Reset overrideEnabled: {self.node}")

    def delete_history(self) -> None:
        """Delete the history of the node."""
        cmds.delete(self.node, constructionHistory=True)
        logger.debug(f"Deleted history: {self.node}")

    def clean(self, **kwargs) -> None:
        """Clean up the node with specified options.

        Keyword Args:
            unlock_attributes (bool): If True, unlock all locked attributes. Default is False.
            delete_user_attributes (bool): If True, delete all user-defined attributes. Default is False.
            remove_from_sets (bool): If True, remove the node from all sets. Default is False.
            apply_initial_shader (bool): If True, apply initial shader to the node. Default is False.
        """
        unlock_attributes_flag = kwargs.get("unlock_attributes", False)
        delete_user_attrs_flag = kwargs.get("delete_user_attributes", False)
        remove_from_sets_flag = kwargs.get("remove_from_sets", False)
        apply_initial_shader_flag = kwargs.get("apply_initial_shader", False)

        if unlock_attributes_flag:
            self.unlock_attributes()
        if delete_user_attrs_flag:
            self.delete_user_attributes()
        if remove_from_sets_flag:
            self.remove_from_sets()
        if apply_initial_shader_flag:
            self.apply_initial_shader()

        logger.debug(f"{self.__class__.__name__}: {self.node}")
