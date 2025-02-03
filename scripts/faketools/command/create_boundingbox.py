"""
Create a bounding box around the selected objects.
"""

from abc import ABC, abstractmethod
from logging import getLogger
from typing import Optional

import maya.cmds as cmds

from ..lib import lib_boundingbox, lib_mesh, lib_transform

logger = getLogger(__name__)


class BoxObject(ABC):
    """Box object class.

    Abstract class for generating Box type objects. Implement the box_object method to generate Box type objects.
    The radius of the Box type object is 0.5.
    """

    @abstractmethod
    def create(self):
        """Create a bounding box object.

        Args:
            base_line (list[float]): The baseline point for each axis. Default is the center of the object.
        """
        pass


class MeshBox(BoxObject):

    def create(self):
        """Create a bounding box object.
        """
        return cmds.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1, ax=[0, 1, 0], cuv=4, ch=False)[0]


class CurveBox(BoxObject):

    def create(self):
        """Create a bounding box object.
        """
        points = [(-0.5, 0.5, 0.5),
                  (0.5, 0.5, 0.5),
                  (0.5, 0.5, -0.5),
                  (-0.5, 0.5, -0.5),
                  (-0.5, 0.5, 0.5),
                  (-0.5, -0.5, 0.5),
                  (-0.5, -0.5, -0.5),
                  (-0.5, 0.5, -0.5),
                  (-0.5, -0.5, -0.5),
                  (0.5, -0.5, -0.5),
                  (0.5, 0.5, -0.5),
                  (0.5, -0.5, -0.5),
                  (0.5, -0.5, 0.5),
                  (0.5, 0.5, 0.5),
                  (0.5, -0.5, 0.5),
                  (-0.5, -0.5, 0.5)]

        return cmds.curve(d=1, p=points, k=[i for i in range(len(points))])


class LocatorBox(BoxObject):

    def create(self):
        """Create a bounding box object.
        """
        return cmds.spaceLocator()[0]


class CreateBoundingBox:

    def __init__(self, bounding_box: lib_boundingbox.BoundingBox):
        """Constructor.

        Args:
            bounding_box (lib_boundingbox.BoundingBox): Bounding box object.
        """
        if not isinstance(bounding_box, lib_boundingbox.BoundingBox):
            raise TypeError('bounding_box must be an instance of BoundingBox class.')

        self._bounding_box = bounding_box

    def create(self, box_object: BoxObject, include_scale: bool = True, base_line: Optional[list[float]] = None):
        """Create a bounding box around the selected objects.

        Args:
            box_object (BoxObject): Box object.
        """
        if not isinstance(box_object, BoxObject):
            raise TypeError('box_object must be an instance of BoxObject class.')

        if base_line == [0.0, 0.0, 0.0]:
            base_line = None

        if base_line is not None:
            if not isinstance(base_line, (list, tuple)):
                raise TypeError('base_line must be a list or tuple.')

            if not all([-1.0 <= val <= 1.0 for val in base_line]):
                raise ValueError('base_line must be in the range of -1.0 to 1.0.')

            base_line = [val * 0.5 for val in base_line]

        box_geometry = box_object.create()

        if base_line is not None:
            cmds.move(*base_line, box_geometry, r=True)
            lib_transform.FreezeTransformNode(box_geometry).freeze(freeze_transform=True, freeze_pivot=True, freeze_vertex=False)

        translate = self._bounding_box.center
        rotate = self._bounding_box.rotation
        scale = self._bounding_box.scale

        cmds.setAttr(f'{box_geometry}.translate', *translate)
        cmds.setAttr(f'{box_geometry}.rotate', *rotate)
        cmds.setAttr(f'{box_geometry}.scale', *scale)

        if base_line is not None:
            cmds.xform(box_geometry, os=True, r=True, t=[val * -1.0 for val in base_line])

        if not include_scale:
            cmds.makeIdentity(box_geometry, apply=True, t=False, r=False, s=True, n=0, pn=False)

        if base_line is not None or not include_scale:
            box_geometry_shp = cmds.listRelatives(box_geometry, s=True, f=True)[0]
            if box_geometry_shp and cmds.objectType(box_geometry_shp) == 'mesh':
                lib_transform.FreezeTransformNode(box_geometry).freeze(freeze_transform=False, freeze_pivot=False, freeze_vertex=True)

        return box_geometry


def main(bounding_box_type: str = 'world', box_type='mesh', include_scale: bool = True, is_parent: bool = False, *args, **kwargs):
    """Create a bounding box around the selected objects.

    Args:
        bounding_box_type (str): Bounding box type. 'world' or 'minimum' or 'axis_aligned'.
        box_type (str): Box type. 'mesh' or 'curve'.
        include_scale (bool): Include scale in the bounding box calculation.
        is_parent (bool): Parent the selected objects to the bounding box object.

    Notes:
        - Bounding box types:
            - world: World bounding box.
            - minimum: Bounding box with the smallest volume.
            - axis_aligned: Bounding box with the smallest volume around the specified axis.
                - Keyword arguments:
                    - axis_direction (Union[list[float], np.ndarray]): The direction vector of the fixed axis.
                    - axis (str): The axis in the local coordinate system to which the fixed axis is assigned.
                        One of "x", "y", or "z". Default is "z" (i.e., axis_direction is assigned to the local Z axis).
                    - theta_sampling (int): The number of divisions to evaluate θ (0 to 2π). Default is 360.
    """
    bounding_box_types = {'world': lib_boundingbox.WorldBoundingBox,
                          'minimum': lib_boundingbox.MinimumBoundingBox,
                          'axis_aligned': lib_boundingbox.AxisAlignedBoundingBox}

    box_types = {'mesh': MeshBox,
                 'curve': CurveBox,
                 'locator': LocatorBox}

    base_line = kwargs.pop('base_line', None)

    sel_nodes = cmds.ls(sl=True, type='transform')
    if not sel_nodes:
        cmds.error('No objects selected.')

    box_obj = box_types[box_type]()

    result_objs = []
    for node in sel_nodes:
        meshs = cmds.listRelatives(node, ad=True, type='mesh')
        if not meshs:
            cmds.warning(f'No mesh found in {node}.')
            continue

        target_points = _get_mesh_points(meshs)
        bounding_box = bounding_box_types[bounding_box_type](target_points, *args, **kwargs)

        create_bounding_box = CreateBoundingBox(bounding_box)
        result_obj = create_bounding_box.create(box_obj, include_scale=include_scale, base_line=base_line)
        result_obj = cmds.rename(result_obj, f'{node}_boundingBox')

        logger.debug(f'Created {result_obj}.')

        if is_parent:
            current_parent = cmds.listRelatives(node, p=True)
            if current_parent:
                cmds.parent(result_obj, current_parent[0])

            cmds.parent(node, result_obj)

            logger.debug(f'Parented {node} to {result_obj}.')

        result_objs.append(result_obj)

    cmds.select(result_objs, r=True)


def _get_mesh_points(meshs: list[str]):
    """Get mesh points.

    Args:
        meshs (list[str]): Mesh list.
    """
    points = []
    for mesh in meshs:
        points.extend(lib_mesh.MeshVertex(mesh).get_vertex_positions(as_float=True))
    return points
