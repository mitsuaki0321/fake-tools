"""
Shape node functions.
"""

from logging import getLogger

import maya.cmds as cmds

logger = getLogger(__name__)


def duplicate_original_shape(shape: str) -> str:
    """Duplicate the original shape nodes.

    Args:
        shape (str): The shape node.

    Returns:
        str: The duplicated original shape node.
    """
    if not cmds.objExists(shape):
        raise ValueError(f'Node does not exist: {shape}')

    if cmds.nodeType(shape) not in ['mesh', 'nurbsSurface', 'nurbsCurve']:
        raise ValueError(f'Unsupported type: {shape}')

    transform = cmds.listRelatives(shape, p=True)[0]

    # Get original shape
    original_shape = get_original_shape(shape)
    if not original_shape:
        raise ValueError(f'Failed to get the original shape: {shape}')

    # Duplicate
    shape_type = cmds.nodeType(shape)
    transform_short_name = transform.split('|')[-1]

    new_shape = cmds.createNode(shape_type, name=f'{transform_short_name}_origShape', ss=True)
    new_transform = cmds.listRelatives(new_shape, p=True)[0]
    new_transform = cmds.rename(new_transform, f'{transform_short_name}_orig')

    # Copy the transform
    mat = cmds.xform(transform, q=True, ws=True, m=True)
    cmds.xform(new_transform, ws=True, m=mat)

    # Copy the shape
    connect_shapes(original_shape, new_shape, only_copy=True)

    # Assign the initial shader
    cmds.sets(new_transform, edit=True, forceElement='initialShadingGroup')

    return new_transform


def get_original_shape(shape: str) -> str:
    """Get the original shape nodes.

    Args:
        shape (str): The shape node.

    Returns:
        str: The original shape node.
    """
    if not cmds.objExists(shape):
        raise ValueError(f'Node does not exist: {shape}')

    input_plug = dict(mesh='inMesh', nurbsSurface='create', nurbsCurve='create')
    shape_type = cmds.nodeType(shape)

    if shape_type not in input_plug:
        raise ValueError(f'Unsupported shape type: {shape_type}')

    plug_chains = cmds.geometryAttrInfo(f'{shape}.{input_plug[shape_type]}', outputPlugChain=True)
    if not plug_chains:
        return shape

    for plug_chain in plug_chains:
        node, _ = plug_chain.split('.')
        if cmds.nodeType(node) == shape_type:
            return node


def copy_topology(src_node: str, dest_node: str) -> None:
    """Copy the topology src_node shape to dest_node original shape.

    Args:
        src_node (str): The source transform node.
        dest_node (str): The destination transform node.
    """
    if not cmds.objExists(src_node):
        raise ValueError(f'Node does not exist: {src_node}')

    if not cmds.objExists(dest_node):
        raise ValueError(f'Node does not exist: {dest_node}')

    if 'transform' not in cmds.nodeType(src_node, inherited=True):
        raise ValueError(f'Node is not a transform: {src_node}')

    if 'transform' not in cmds.nodeType(dest_node, inherited=True):
        raise ValueError(f'Node is not a transform: {dest_node}')

    src_shapes = cmds.listRelatives(src_node, s=True, path=True)
    dest_shapes = cmds.listRelatives(dest_node, s=True, path=True)

    if not src_shapes:
        raise ValueError(f'No shape found: {src_node}')

    if not dest_shapes:
        raise ValueError(f'No shape found: {dest_node}')

    if cmds.nodeType(src_shapes[0]) != cmds.nodeType(dest_shapes[0]):
        raise ValueError(f'Different shape type: {src_shapes[0]} != {dest_shapes[0]}')

    original_shape = get_original_shape(dest_shapes[0])
    if not original_shape:
        raise ValueError(f'Failed to get the original shape: {dest_shapes[0]}')

    connect_shapes(src_shapes[0], original_shape, only_copy=True)

    logger.debug(f'Copied topology: {src_shapes[0]} -> {original_shape}')


def connect_shapes(src_shape: str, dest_shape: str, **kwargs) -> None:
    """Connect or copy the shapes.

    Args:
        src_shape (str): The source shape node.
        dest_shape (str): The destination shape node.

    Keyword Args:
        only_copy (bool): Whether to only copy the shapes. Default is False.
        force_connect (bool): Whether to force connect the shapes. Default is False.

    Raises:
        ValueError: If the source shape is already connected.If the force_connect is False.
    """
    if not cmds.objExists(src_shape):
        raise ValueError(f'Node does not exist: {src_shape}')

    if not cmds.objExists(dest_shape):
        raise ValueError(f'Node does not exist: {dest_shape}')

    if 'surfaceShape' not in cmds.nodeType(src_shape, inherited=True):
        raise ValueError(f'Node is not a shape: {src_shape}')

    if 'surfaceShape' not in cmds.nodeType(dest_shape, inherited=True):
        raise ValueError(f'Node is not a shape: {dest_shape}')

    src_node_type = cmds.nodeType(src_shape)
    dest_node_type = cmds.nodeType(dest_shape)

    if src_node_type != dest_node_type:
        raise ValueError(f'Different shape type: {src_node_type} != {dest_node_type}')

    if src_node_type not in ['mesh', 'nurbsSurface', 'nurbsCurve']:
        raise ValueError(f'Unsupported shape type: {src_shape} and {dest_shape}')

    only_copy = kwargs.get('only_copy', False)
    force_connect = kwargs.get('force', False)

    shape_plugs = {'mesh': ['outMesh', 'inMesh'],
                   'nurbsSurface': ['local', 'create'],
                   'nurbsCurve': ['local', 'create']}

    src_plugs = cmds.listConnections(f'{src_shape}.{shape_plugs[src_node_type][1]}', s=True, d=False)
    if not force_connect and src_plugs:
        raise ValueError(f'Source shape is already connected: {src_shape}')

    cmds.connectAttr(f'{src_shape}.{shape_plugs[src_node_type][0]}', f'{dest_shape}.{shape_plugs[dest_node_type][1]}', f=True)
    if only_copy:
        cmds.refresh()
        cmds.disconnectAttr(f'{src_shape}.{shape_plugs[src_node_type][0]}', f'{dest_shape}.{shape_plugs[dest_node_type][1]}')
        cmds.refresh()
        logger.debug(f'Copied shapes: {src_shape} -> {dest_shape}')
    else:
        logger.debug(f'Connected shapes: {src_shape} -> {dest_shape}')


def check_topology(src_shape: str, dest_shape: str) -> bool:
    """Check the topology.

    Args:
        src_shape (str): The source shape node.
        dest_shape (str): The destination shape node.

    Returns:
        bool: Whether the topology is the same.
    """
    if not cmds.objExists(src_shape):
        raise ValueError(f'Node does not exist: {src_shape}')

    if not cmds.objExists(dest_shape):
        raise ValueError(f'Node does not exist: {dest_shape}')

    src_node_type = cmds.nodeType(src_shape)
    dest_node_type = cmds.nodeType(dest_shape)

    if src_node_type != dest_node_type:
        raise ValueError(f'Different node type: {src_node_type} != {dest_node_type}')

    if src_node_type not in ['mesh', 'nurbsSurface', 'nurbsCurve']:
        raise ValueError(f'Unsupported shape type: {src_shape} and {dest_shape}')

    if src_node_type == 'mesh':
        src_vtx_count = cmds.polyEvaluate(src_shape, v=True)
        dest_vtx_count = cmds.polyEvaluate(dest_shape, v=True)

        if src_vtx_count != dest_vtx_count:
            logger.debug(f'Different vertex count: {src_shape} != {dest_shape}')
            return False

        src_edge_count = cmds.polyEvaluate(src_shape, e=True)
        dest_edge_count = cmds.polyEvaluate(dest_shape, e=True)

        if src_edge_count != dest_edge_count:
            logger.debug(f'Different edge count: {src_shape} != {dest_shape}')
            return False

        src_face_count = cmds.polyEvaluate(src_shape, f=True)
        dest_face_count = cmds.polyEvaluate(dest_shape, f=True)

        if src_face_count != dest_face_count:
            logger.debug(f'Different face count: {src_shape} != {dest_shape}')
            return False

        return True
    elif src_node_type == 'nurbsSurface':
        src_spans_u = cmds.getAttr(f'{src_shape}.spansU')
        dest_spans_u = cmds.getAttr(f'{dest_shape}.spansU')

        if src_spans_u != dest_spans_u:
            logger.debug(f'Different spansU: {src_shape} != {dest_shape}')
            return False

        src_spans_v = cmds.getAttr(f'{src_shape}.spansV')
        dest_spans_v = cmds.getAttr(f'{dest_shape}.spansV')

        if src_spans_v != dest_spans_v:
            logger.debug(f'Different spansV: {src_shape} != {dest_shape}')
            return False

        return True
    elif src_node_type == 'nurbsCurve':
        src_degree = cmds.getAttr(f'{src_shape}.degree')
        dest_degree = cmds.getAttr(f'{dest_shape}.degree')

        if src_degree != dest_degree:
            logger.debug(f'Different degree: {src_shape} != {dest_shape}')
            return False

        src_spans = cmds.getAttr(f'{src_shape}.spans')
        dest_spans = cmds.getAttr(f'{dest_shape}.spans')

        if src_spans != dest_spans:
            logger.debug(f'Different spans: {src_shape} != {dest_shape}')
            return False

        return True
    else:
        raise ValueError(f'Unsupported shape type: {src_node_type}')
