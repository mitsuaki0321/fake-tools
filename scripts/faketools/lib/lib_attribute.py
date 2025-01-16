"""
Maya attribute functions.
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds


def is_modifiable(node: str, attribute: str, **kwargs) -> bool:
    """Returns whether the attribute is modifiable.

    Args:
        node (str): The node name.
        attribute (str): The attribute name.

    Keyword Args:
        children (bool): Whether to check children attributes. Default is False.

    Notes:
        - The static writable flag is not checked, so it may return False even if the attribute is actually not modifiable.

    Raises:
        ValueError: If the node or attribute does not exist.

    Returns:
        bool: Whether the attribute is modifiable.
    """
    if not cmds.objExists(node):
        raise ValueError(f'Node does not exist: {node}')

    if not cmds.attributeQuery(attribute, node=node, exists=True):
        raise ValueError(f'Attribute does not exist: {node}.{attribute}')

    children = kwargs.get('children', False)

    sel = om.MSelectionList()
    sel.add(node)
    obj = sel.getDependNode(0)
    fn = om.MFnDependencyNode(obj)
    try:
        plug = fn.findPlug(attribute, False)
    except RuntimeError:
        return False

    return not bool(plug.isFreeToChange(checkAncestors=True, checkChildren=children))
