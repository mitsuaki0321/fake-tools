"""
Driven key utility commands.
"""

from logging import getLogger

import maya.cmds as cmds

from ..lib import lib_keyframe

logger = getLogger(__name__)


def cleanup_driven_keys(node: str) -> None:
    """Cleanup the driven keys.

    Args:
        node (str): The node name.
    """
    if not node:
        raise ValueError("Invalid node name")

    if not cmds.objExists(node):
        raise ValueError(f"Invalid node. Not exists: {node}")

    driven_plugs = cmds.setDrivenKeyframe(node, q=True, driven=True)
    if not driven_plugs:
        logger.debug(f"No driven keys found: {node}")
        return

    def __check_deletable(anim_curve_node: str) -> bool:
        """Check if the animation curve is deletable.

        Notes:
            - Deletable if all values are the same and all tangent weights are 0.0.

        Returns:
            bool: True if deletable. False otherwise.
        """
        values = cmds.keyframe(anim_curve_node, q=True, valueChange=True)
        tangent_weights = cmds.keyTangent(anim_curve_node, q=True, inAngle=True, outAngle=True)

        return bool(len(list(set(values))) == 1 and not any(tangent_weights))

    for driven_plug in driven_plugs:
        driven_source_plugs = cmds.listConnections(driven_plug, s=True, d=False, p=True)
        driven_source_node = cmds.ls(driven_source_plugs, objectsOnly=True)[0]
        if cmds.nodeType(driven_source_node) not in ["animCurveUU", "animCurveUL", "animCurveUA", "animCurveUT", "blendWeighted"]:
            continue

        if cmds.nodeType(driven_source_node) == "blendWeighted":
            blendWeighted_node = driven_source_node

            anim_curve_plugs = cmds.listConnections(f"{blendWeighted_node}.input", s=True, d=False, p=True, type="animCurve")
            if not anim_curve_plugs:
                cmds.delete(blendWeighted_node)
                logger.debug(f"Deleted blendWeighted node. Not found blendWeighted input nodes: {blendWeighted_node}")
                continue

            anim_curve_nodes = cmds.ls(anim_curve_plugs, objectsOnly=True)
            anim_curve_deleted_nodes = []
            for anim_curve_node in anim_curve_nodes:
                if __check_deletable(anim_curve_node):
                    cmds.delete(anim_curve_node)
                    anim_curve_deleted_nodes.append(anim_curve_node)
                    logger.debug(f"Deleted animation curve node: {anim_curve_node}")

            if len(anim_curve_deleted_nodes) == len(anim_curve_nodes) or not anim_curve_deleted_nodes:
                continue

            dif_anim_curve_nodes = list(set(anim_curve_nodes) - set(anim_curve_deleted_nodes))
            if len(dif_anim_curve_nodes) == 1:
                cmds.connectAttr(f"{dif_anim_curve_nodes[0]}.output", driven_plug, f=True)
                cmds.delete(blendWeighted_node)

                logger.debug(f"Deleted blendWeighted node: {blendWeighted_node}")
        else:
            print(driven_source_node)
            if __check_deletable(driven_source_node):
                cmds.delete(driven_source_node)
                logger.debug(f"Deleted animation curve node: {driven_source_node}")

    logger.debug(f"Cleanup driven keys: {node}")


def mirror_transform_anim_curve(transform: str, time_attrs: list[str] | None, value_attrs: list[str] | None) -> None:
    """Mirror the transform animation curve.

    Args:
        transform (str): The transform node.
        time_attrs (list[str]): The time attributes to mirror.
        value_attrs (list[str]): The value attributes to mirror.
    """
    if not transform:
        raise ValueError("Invalid transform node")

    if not cmds.objExists(transform):
        raise ValueError(f"Transform does not exists: {transform}")

    if "transform" not in cmds.nodeType(transform, inherited=True):
        raise ValueError(f"Invalid transform type: {transform}")

    if not time_attrs and not value_attrs:
        cmds.warning("No options to mirror. Please set mirror axis options.")
        return

    transform_attrs = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]

    invalid_attrs = []
    if time_attrs:
        for attr in time_attrs:
            if attr not in transform_attrs:
                invalid_attrs.append(attr)
    else:
        time_attrs = []

    if value_attrs:
        for attr in value_attrs:
            if attr not in transform_attrs:
                invalid_attrs.append(attr)
    else:
        value_attrs = []

    if invalid_attrs:
        cmds.error(f"Invalid attributes. Please set transform long name: {invalid_attrs}")

    driven_plugs = cmds.setDrivenKeyframe(transform, q=True, driven=True)
    if not driven_plugs:
        cmds.warning(f"No driven keys found: {transform}")
        return

    for driven_plug in driven_plugs:
        driven_attr = cmds.listAttr(driven_plug)[0]
        attr_anim_curve = lib_keyframe.AttributeAnimCurve(driven_plug=driven_plug)
        anim_curves = attr_anim_curve.get_anim_curves()

        for anim_curve in anim_curves:
            mirror_time = driven_attr in time_attrs
            mirror_value = driven_attr in value_attrs
            if not mirror_time and not mirror_value:
                continue
            lib_keyframe.mirror_anim_curve(anim_curve, mirror_time=mirror_time, mirror_value=mirror_value)


def get_driven_key_nodes() -> list[str]:
    """Get the driven key nodes.

    Notes:
        - If no nodes are selected, get all transform nodes.

    Returns:
        list[str]: The driven key nodes.
    """
    sel_nodes = cmds.ls(sl=True)
    if not sel_nodes:
        sel_nodes = cmds.ls(type="transform")

    driven_key_nodes = []
    for sel_node in sel_nodes:
        driven_plugs = cmds.setDrivenKeyframe(sel_node, q=True, driven=True)
        if not driven_plugs:
            continue

        driven_key_nodes.append(sel_node)

    return driven_key_nodes
