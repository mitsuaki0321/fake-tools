"""Single commands.

Scene commands:
    - OptimizeScene

All commands:
    - LockAndHide
    - UnlockAndShow
    - ZeroOutChannelBox
    - BreakConnections
    - FreezeVertices
    - FreezeImmediateVertices
    - ParentConstraint
    - DeleteConstraint
    - ChainJoints
    - MirrorJoints
    - DeleteDynamicAttributes

Pair commands:
    - SnapPosition
    - SnapRotation
    - SnapScale
    - SnapTranslateAndRotate
    - CopyTransform
    - CopyWeight
    - ConnectTopology
    - CopyTopology
    - Parent
"""

from logging import getLogger

import maya.cmds as cmds

from .. import user_directory
from ..lib import lib_attribute, lib_shape, lib_transform
from ..lib.lib_singleCommand import AllCommand, PairCommand, SceneCommand
from ..lib_ui import maya_ui
from . import convert_weight, rigging_setup, scene_optimize

logger = getLogger(__name__)


global_settings = user_directory.ToolSettings(__name__).load()
MIRROR_JOINTS = global_settings.get("MIRROR_JOINTS", ["_L", "_R"])


SCENE_COMMANDS = ("OptimizeScene",)

ALL_COMMANDS = (
    "LockAndHide",
    "UnlockAndShow",
    "ZeroOutChannelBox",
    "BreakConnections",
    "FreezeTransform",
    "FreezeVertices",
    "FreezeImmediateVertices",
    "ParentConstraint",
    "DeleteConstraint",
    "ChainJoints",
    "MirrorJoints",
    "DeleteDynamicAttributes",
)

PAIR_COMMANDS = (
    "SnapPosition",
    "SnapRotation",
    "SnapScale",
    "SnapTranslateAndRotate",
    "CopyTransform",
    "ConnectTransform",
    "CopyWeight",
    "ConnectTopology",
    "CopyTopology",
    "Parent",
)


#
# Scene commands
#


class OptimizeScene(SceneCommand):
    def execute(self):
        """Optimize the scene."""
        scene_optimize.OptimizeUnknownPlugins().execute()
        scene_optimize.OptimizeUnknownNodes().execute()
        scene_optimize.OptimizeUnusedNodes().execute()
        scene_optimize.OptimizeDataStructure().execute()

        logger.debug("Optimized the scene")


#
# All commands
#


class LockAndHide(AllCommand):
    def execute(self, nodes: list[str]):
        """Lock and hide the nodes.

        Notes:
            - Locks and hides all the attributes of the nodes.
            - If selected channels are specified, only those channels will be locked and hidden.
            - If the attribute is visibility, it will not be locked.
        """
        attrs = maya_ui.get_channels()

        def __get_channel_box_attrs(node: str) -> list[str]:
            """Get the channel box attributes."""
            keyable_attrs = cmds.listAttr(node, keyable=True) or []
            non_keyable_attrs = cmds.listAttr(node, channelBox=True) or []
            return keyable_attrs + non_keyable_attrs

        for node in nodes:
            if not attrs:
                attrs = __get_channel_box_attrs(node)

            for attr in attrs:
                if not cmds.attributeQuery(attr, node=node, exists=True):
                    logger.debug(f"Attribute does not exist: {node}.{attr}")
                    continue

                if attr == "visibility":
                    cmds.setAttr(f"{node}.{attr}", lock=False, keyable=False)
                else:
                    cmds.setAttr(f"{node}.{attr}", lock=True, keyable=False, channelBox=False)

                logger.debug(f"Locked and hidden: {node}.{attr}")


class UnlockAndShow(AllCommand):
    def execute(self, nodes: list[str]):
        """Restore the channel box display of the nodes to the state when they were created."""
        node_type_map = {}
        for node in nodes:
            node_type = cmds.nodeType(node)
            node_type_map.setdefault(node_type, []).append(node)

        for node_type, nodes in node_type_map.items():
            tmp_node = cmds.createNode(node_type, ss=True)
            keyable_attrs = cmds.listAttr(tmp_node, keyable=True) or []  # Get keyable attributes
            non_keyable_attrs = cmds.listAttr(tmp_node, channelBox=True) or []  # Get non-keyable attributes displayed in the channel box
            locked_attrs = cmds.listAttr(tmp_node, locked=True) or []  # Get locked attributes
            for node in nodes:
                for attr in keyable_attrs:
                    if not cmds.attributeQuery(attr, node=node, exists=True):
                        logger.debug(f"Attribute does not exist: {node}.{attr}")
                        continue

                    cmds.setAttr(f"{node}.{attr}", keyable=True, channelBox=False)
                    if attr in locked_attrs:
                        cmds.setAttr(f"{node}.{attr}", lock=True)
                    else:
                        cmds.setAttr(f"{node}.{attr}", lock=False)

                for attr in non_keyable_attrs:
                    if not cmds.attributeQuery(attr, node=node, exists=True):
                        logger.debug(f"Attribute does not exist: {node}.{attr}")
                        continue

                    cmds.setAttr(f"{node}.{attr}", keyable=False, channelBox=True)
                    if attr in locked_attrs:
                        cmds.setAttr(f"{node}.{attr}", lock=True)
                    else:
                        cmds.setAttr(f"{node}.{attr}", lock=False)

                logger.debug(f"Unlocked and shown: {node}")

            cmds.delete(tmp_node)


class ZeroOutChannelBox(AllCommand):
    def execute(self, nodes: list[str]):
        """Zero out the nodes.

        Notes:
            - Zero out the nodes.
        """
        for node in nodes:
            attrs = lib_attribute.get_channelBox_attr(node)
            if not attrs:
                cmds.warning("No channelBox attributes: {node}")
                return

            rigging_setup.zero_out_attributes(node, attrs)


class BreakConnections(AllCommand):
    def execute(self, nodes: list[str]):
        """Break all connections of the nodes.

        Notes:
            - Break connection of selected channels.
        """
        attrs = maya_ui.get_channels()
        if not attrs:
            cmds.warning("No channels selected")
            return

        parent_attrs = []
        for attr in attrs:
            parent_attr = cmds.attributeQuery(attr, node=nodes[0], listParent=True)
            if parent_attr:
                parent_attrs.append(parent_attr[0])

        if parent_attrs:
            attrs += parent_attrs

        for node in nodes:
            for attr in attrs:
                if not cmds.attributeQuery(attr, node=node, exists=True):
                    logger.debug(f"Attribute does not exist: {node}.{attr}")
                    continue

                plug = f"{node}.{attr}"
                source_plug = cmds.listConnections(plug, s=True, d=False, p=True)
                if not source_plug:
                    logger.debug(f"No connection: {plug}")
                    continue

                cmds.disconnectAttr(source_plug[0], plug)

                logger.debug(f"Broke connection: {source_plug[0]} -> {plug}")


class FreezeTransform(AllCommand):
    def execute(self, nodes: list[str]):
        """Freeze the transform of the nodes.

        Notes:
            - Freeze the transform of the nodes.
        """
        for node in nodes:
            lib_transform.FreezeTransformNode(node).freeze(freeze_transform=True, freeze_pivot=True, freeze_vertex=False)


class FreezeVertices(AllCommand):
    def execute(self, nodes: list[str]):
        """Freeze the vertices of the nodes.

        Notes:
            - Freeze the vertices of the nodes.
            - The nodes must have a shape node.
        """
        sel_nodes = cmds.ls(sl=True)

        for node in nodes:
            lib_transform.FreezeTransformNode(node).freeze(freeze_transform=False, freeze_pivot=False, freeze_vertex=True)

        if sel_nodes:
            cmds.select(sel_nodes, r=True)


class FreezeImmediateVertices(AllCommand):
    def execute(self, nodes: list[str]):
        """Freeze the immediate vertices of the nodes.

        Notes:
            - Freeze the immediate vertices of the nodes.
            - The nodes must have a shape node.
        """
        sel_nodes = cmds.ls(sl=True)

        for node in nodes:
            shape = cmds.listRelatives(node, s=True, f=True, ni=True)
            if not shape:
                logger.debug(f"No shape: {node}")
                continue

            immediate_shape = lib_shape.get_original_shape(shape[0])
            if not immediate_shape:
                logger.debug(f"No immediate shape: {shape[0]}")
                continue

            cmds.cluster(immediate_shape)
            cmds.delete(immediate_shape, ch=True)

            logger.debug(f"Freezed immediate vertices: {node}")

        if sel_nodes:
            cmds.select(sel_nodes, r=True)


class ParentConstraint(AllCommand):
    def execute(self, nodes: list[str]):
        """Create a parent constraint.

        Notes:
            - Create a target locator and use it to create a parent constraint.
        """
        for node in nodes:
            lock_locator = cmds.spaceLocator(n=f"{node}_parentConstraint_locator")[0]
            pos = cmds.xform(node, q=True, ws=True, t=True)
            rot = cmds.xform(node, q=True, ws=True, ro=True)
            cmds.xform(lock_locator, ws=True, t=pos, ro=rot)

            cmds.parentConstraint(lock_locator, node, mo=True)

            logger.debug(f"Created parent constraint: {lock_locator} -> {node}")


class DeleteConstraint(AllCommand):
    def execute(self, nodes: list[str]):
        """Delete the constraints of the nodes.

        Notes:
            - Delete all constraints of the nodes.
        """
        for node in nodes:
            cmds.delete(node, constraints=True)

            logger.debug(f"Deleted constraints: {node}")


class ChainJoints(AllCommand):
    def execute(self, nodes: list[str]):
        """Chain the joints."""
        if len(nodes) < 2:
            cmds.warning("Select at least 2 nodes")
            return

        # Check root parent node
        nodes = cmds.ls(nodes, l=True)
        root_parent_node = cmds.listRelatives(nodes[0], p=True, f=True)
        is_root_node_world = False
        if root_parent_node:
            parent_node = root_parent_node[0]
            parent_nodes = [parent_node]
            while True:
                parent_node = cmds.listRelatives(parent_node, p=True, f=True)
                if not parent_node:
                    break
                parent_nodes.append(parent_node[0])

            parent_nodes = list(reversed(parent_nodes))
            for index, parent_node in enumerate(parent_nodes):
                if parent_node in nodes:
                    if index == 0:
                        root_parent_node = None
                    else:
                        root_parent_node = parent_nodes[index - 1]
                    break
        else:
            is_root_node_world = True

        # Create dummy parent nodes
        dummy_parent_nodes = []
        uuids = cmds.ls(nodes, uuid=True)
        for uuid in uuids:
            node = cmds.ls(uuid)[0]
            parent = cmds.listRelatives(node, p=True)
            if parent:
                mat = cmds.xform(node, q=True, ws=True, m=True)
                dummy = cmds.createNode("transform", ss=True)
                cmds.xform(dummy, ws=True, m=mat)
                cmds.parent(node, dummy)
                dummy_parent_nodes.append(dummy)

        # Chain transforms
        for i in range(len(uuids) - 1):
            uuid_nodes = cmds.ls([uuids[i + 1], uuids[i]])
            cmds.parent(*uuid_nodes)

        root_node = cmds.ls(uuids[0])[0]
        if root_parent_node:
            cmds.parent(root_node, root_parent_node)
        elif not is_root_node_world:
            cmds.parent(root_node, w=True)

        if dummy_parent_nodes:
            cmds.delete(dummy_parent_nodes)

        root_node = cmds.ls(uuids[0])[0]
        cmds.select(root_node, r=True)

        logger.debug(f"Chained joints: {nodes}")


class MirrorJoints(AllCommand):
    def execute(self, nodes: list[str]):
        """Mirror the joints."""
        if len(nodes) < 1:
            cmds.warning("Select more than 1 node")
            return

        for node in nodes:
            if cmds.nodeType(node) != "joint":
                cmds.warning(f"Not a joint: {node}")
                continue

            mirror_node = cmds.mirrorJoint(node, mirrorBehavior=True, mirrorYZ=True, searchReplace=MIRROR_JOINTS)

            logger.debug(f"Mirrored joints: {node} -> {mirror_node}")


class DeleteDynamicAttributes(AllCommand):
    def execute(self, nodes: list[str]):
        """Delete the dynamic attributes of the nodes.

        Notes:
            - Delete all dynamic attributes of the nodes.
        """
        for node in nodes:
            attrs = cmds.listAttr(node, ud=True) or []
            for attr in attrs:
                cmds.setAttr(f"{node}.{attr}", lock=False)
                cmds.deleteAttr(f"{node}.{attr}")

                logger.debug(f"Deleted dynamic attribute: {node}.{attr}")


#
# Pair commands
#


class SnapPosition(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Snap the position of the source to the target."""
        cmds.xform(target_node, ws=True, t=cmds.xform(source_node, q=True, ws=True, t=True))

        logger.debug(f"Snapped position: {target_node} -> {source_node}")


class SnapRotation(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Snap the rotation of the source to the target."""
        cmds.xform(target_node, ws=True, ro=cmds.xform(source_node, q=True, ws=True, ro=True))

        logger.debug(f"Snapped rotation: {target_node} -> {source_node}")


class SnapScale(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Snap the scale of the source to the target."""
        cmds.xform(target_node, ws=True, s=cmds.xform(source_node, q=True, ws=True, s=True))

        logger.debug(f"Snapped scale: {target_node} -> {source_node}")


class SnapTranslateAndRotate(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Snap the position and rotation of the source to the target."""
        cmds.xform(target_node, ws=True, t=cmds.xform(source_node, q=True, ws=True, t=True))
        cmds.xform(target_node, ws=True, ro=cmds.xform(source_node, q=True, ws=True, ro=True))

        logger.debug(f"Snapped translate and rotate: {target_node} -> {source_node}")


class CopyTransform(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Copy the transform of the source to the target."""
        for attr in ["translate", "rotate", "scale"]:
            target_attrs = cmds.attributeQuery(attr, node=source_node, listChildren=True)
            target_attrs += [attr]

            if any([cmds.getAttr(f"{target_node}.{attr}", lock=True) for attr in target_attrs]):
                cmds.warning(f"Skip copy transform. Locked attribute: {target_node}.{attr}")
                continue

            value = cmds.getAttr(f"{source_node}.{attr}")[0]
            cmds.setAttr(f"{target_node}.{attr}", *value)

            logger.debug(f"Copied transform: {source_node} -> {target_node}")


class ConnectTransform(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Connect the transform of the source to the target."""
        for attr in ["translate", "rotate", "scale"]:
            source_attrs = cmds.attributeQuery(attr, node=source_node, listChildren=True)

            for source_attr in source_attrs:
                if not cmds.attributeQuery(source_attr, node=target_node, exists=True):
                    logger.debug(f"Attribute does not exist: {target_node}.{source_attr}")
                    continue

                source_plug = f"{source_node}.{source_attr}"
                target_plug = f"{target_node}.{source_attr}"

                if cmds.isConnected(source_plug, target_plug):
                    logger.debug(f"Already connected: {source_plug} -> {target_plug}")
                    continue

                lock_state = cmds.getAttr(target_plug, lock=True)
                if lock_state:
                    cmds.setAttr(target_node, lock=False)

                cmds.connectAttr(source_plug, target_plug, f=True)

                if lock_state:
                    cmds.setAttr(target_node, lock=True)
                    logger.debug(f"Unlocked and connected due to locked state: {source_plug} -> {target_plug}")

                logger.debug(f"Connected transform: {source_plug} -> {target_plug}")


class CopyWeight(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Copy the weight of the source to the target."""
        convert_weight.copy_skin_weights_with_bind(source_node, [target_node])

        logger.debug(f"Copied weight: {source_node} -> {target_node}")


class ConnectTopology(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Connect the topology of the source to the target."""
        source_shapes = cmds.listRelatives(source_node, s=True, path=True, ni=True)
        target_shapes = cmds.listRelatives(target_node, s=True, path=True, ni=True)

        if not source_shapes:
            raise ValueError(f"No shape found: {source_node}")

        if not target_shapes:
            raise ValueError(f"No shape found: {target_node}")

        lib_shape.connect_shapes(source_shapes[0], target_shapes[0])

        logger.debug(f"Connected topology: {source_node} -> {target_node}")


class CopyTopology(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Copy the topology of the source to the target."""
        source_shapes = cmds.listRelatives(source_node, s=True, path=True, ni=True)
        target_shapes = cmds.listRelatives(target_node, s=True, path=True, ni=True)

        if not source_shapes:
            raise ValueError(f"No shape found: {source_node}")

        if not target_shapes:
            raise ValueError(f"No shape found: {target_node}")

        lib_shape.connect_shapes(source_shapes[0], target_shapes[0], only_copy=True)

        logger.debug(f"Copied topology: {source_node} -> {target_node}")


class Parent(PairCommand):
    def execute(self, source_node: str, target_node: str):
        """Parent the source to the target."""
        parent_node = cmds.listRelatives(source_node, p=True)
        if parent_node and parent_node[0] == target_node:
            cmds.warning(f"Already parented: {source_node} -> {target_node}")
            return

        cmds.parent(source_node, target_node)

        logger.debug(f"Parented: {source_node} -> {target_node}")
