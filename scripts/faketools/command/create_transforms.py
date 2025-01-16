"""
Create transform nodes at selected object's position.
"""

import math
from logging import getLogger
from typing import Optional

import maya.api.OpenMaya as om
import maya.cmds as cmds

from ..lib import (
    lib_component,
    lib_conversion,
    lib_math,
    lib_mesh,
    lib_nurbsCurve,
    lib_nurbsSurface,
    lib_preview,
)

logger = getLogger(__name__)


class CreateTransforms:
    """Create transform nodes at positions.
    """

    __shape_types = ['locator', 'joint']

    def __init__(self,
                 func: callable,
                 size: float = 1.0,
                 shape_type: str = 'locator',
                 chain: bool = False,
                 reverse: bool = False,
                 rotation_offset: list[float] = [0.0, 0.0, 0.0]):
        """Constructor.

        Args:
            func (callable): The function to get the position and rotation.
            size (float): The size of the transform node. Default is 1.0.
            shape_type (str): The shape type of the transform node. Default is 'locator'.
            chain (bool): Whether to chain the transform node. Default is False.
            reverse (bool): Whether to reverse the transform node. Default is False.
            rotation_offset (list[float]): The rotation to add to the current rotation. Default is [0.0, 0.0, 0.0].
        """
        if shape_type not in self.__shape_types:
            raise ValueError('Invalid shape type.')

        self.func = func

        self.size = size
        self.shape_type = shape_type
        self.chain = chain
        self.reverse = reverse
        self.rotation_offset = rotation_offset

    def create(self, *args, **kwargs) -> list[str]:
        """Create the transform nodes.
        """
        position_rotations = self.func(*args, **kwargs)  # [{'position': [], 'rotation': []}, ...]
        if not position_rotations:
            cmds.error('No valid object selected ( component or transform ).')
            return

        result_nodes = []
        for data in position_rotations:
            positions = data['position']
            rotations = data['rotation']

            if self.reverse:
                positions.reverse()

                if rotations:
                    rotations.reverse()

            if rotations and self.rotation_offset != [0.0, 0.0, 0.0]:
                rotations = [lib_math.mult_rotation([self.rotation_offset, rotation]) for rotation in rotations]

            make_nodes = []
            for i in range(len(positions)):
                # Create a transform node and set the size
                if self.shape_type == 'locator':
                    shp = cmds.createNode(self.shape_type, ss=True)
                    node = cmds.listRelatives(shp, p=True)[0]

                    cmds.setAttr(f'{shp}.localScale', self.size, self.size, self.size)

                elif self.shape_type == 'joint':
                    node = cmds.createNode(self.shape_type, ss=True)
                    cmds.setAttr(f'{node}.radius', self.size)

                # Set position and rotation
                cmds.xform(node, ws=True, t=positions[i])

                if rotations:
                    cmds.xform(node, ws=True, ro=rotations[i])

                make_nodes.append(node)

            if self.chain:
                for i in range(len(make_nodes) - 1):
                    cmds.parent(make_nodes[i + 1], make_nodes[i])

            result_nodes.extend(make_nodes)

        logger.debug(f'Transform nodes created: {result_nodes}')

        return result_nodes


class PreviewLocatorForTransform:
    """Preview locator for create transform nodes.
    """

    preview_locator_name = 'createTransformPreview'
    __shape_types = ['locator', 'joint']

    def __init__(self,
                 func: callable,
                 size: float = 1.0,
                 shape_type: str = 'locator',
                 chain: bool = False,
                 reverse: bool = False,
                 rotation_offset: list[float] = [0.0, 0.0, 0.0],
                 color: list[float] = [1.0, 1.0, 1.0]):
        """Constructor.

        Args:
            func (callable): The function to get the position and rotation.
            size (float): The size of the preview locator. Default is 1.0.
            shape_type (str): The shape type of the preview locator. Default is 'locator'.
            chain (bool): Whether to chain the preview locator. Default is False.
            reverse (bool): Whether to reverse the preview locator. Default is False.
            rotation_offset (list[float]): The rotation to add to the current rotation. Default is [0.0, 0.0, 0.0].
            color (list[float]): The color of the preview locator. Default is [1.0, 1.0, 1.0].
        """
        if shape_type not in self.__shape_types:
            raise ValueError('Invalid shape type.')

        self.func = func

        self.size = size
        self.shape_type = shape_type
        self.chain = chain
        self.reverse = reverse
        self.rotation_offset = rotation_offset
        self.color = color

        self.preview_locator = lib_preview.PreviewLocator.create(name=self.preview_locator_name, recreate=True)

    def preview(self, *args, **kwargs):
        """Preview the transform.
        """
        position_rotations = self.func(*args, **kwargs)  # [{'position': [], 'rotation': []}, ...]
        if not position_rotations:
            self.preview_locator.clear_shapes()
            logger.warning('No valid position and rotation data for preview.')
            return

        self.preview_locator.manipulation_color = True

        # Set the shape type
        self.preview_locator.shape_type = self.shape_type

        logger.debug(f'Shape type: {self.shape_type}')

        # Set the size
        self.preview_locator.global_size = self.size

        logger.debug(f'Size: {self.size}')

        # Set the position and rotation
        num_data = len(position_rotations)

        for i in range(num_data):
            positions = position_rotations[i]['position']
            rotations = position_rotations[i]['rotation']

            if positions:
                if self.reverse:
                    positions.reverse()

                    logger.debug(f'Reverse positions: {self.reverse}')

                self.preview_locator.set_shape_positions(index=i, positions=positions)

            if rotations:
                if self.reverse:
                    rotations.reverse()

                    logger.debug(f'Reverse rotations: {self.reverse}')

                if self.rotation_offset != [0.0, 0.0, 0.0]:
                    rotations = [lib_math.mult_rotation([self.rotation_offset, rotation]) for rotation in rotations]

                    logger.debug(f'Rotation offset: {self.rotation_offset}')

                self.preview_locator.set_shape_rotations(index=i, rotations=rotations)

            if self.chain:
                self.preview_locator.set_shape_hierarchy(index=i, value=True)

                logger.debug(f'Chain: {self.chain}')

            if self.color != [1.0, 1.0, 1.0]:
                self.preview_locator.set_shape_color(index=i, color=self.color)

                logger.debug(f'Color: {self.color}')

        logger.debug(f'Preview created: {self.preview_locator}')

    def change_function(self, func: callable):
        """Change the function of the previewLocator.
        """
        self.func = func
        self.preview_locator.clear_shapes()

        logger.debug(f'Function changed: {func}')

    def change_size(self, size: float):
        """Change the size of the previewLocator.
        """
        if not self.preview_locator:
            return

        if self.size == size:
            return

        self.preview_locator.global_size = size
        self.size = size

        logger.debug(f'Size changed: {size}')

    def change_shape_type(self, shape_type: str):
        """Change the shape type of the previewLocator.
        """
        if not self.preview_locator:
            return

        if shape_type not in ['locator', 'joint']:
            raise ValueError('Invalid shape type.')

        if self.shape_type == shape_type:
            return

        self.preview_locator.shape_type = shape_type
        self.shape_type = shape_type

        logger.debug(f'Shape type changed: {shape_type}')

    def change_chain(self, chain: bool):
        """Change the chain of the previewLocator.
        """
        if not self.preview_locator:
            return

        if self.chain == chain:
            return

        if not self.preview_locator.num_shapes:
            return

        for i in range(self.preview_locator.num_shapes):
            self.preview_locator.set_shape_hierarchy(index=i, value=chain)

        self.chain = chain

        logger.debug(f'Chain changed: {chain}')

    def change_reverse(self, reverse: bool):
        """Change the reverse of the previewLocator.
        """
        if not self.preview_locator:
            return

        if not self.preview_locator.num_shapes:
            return

        if self.reverse == reverse:
            return

        for i in range(self.preview_locator.num_shapes):
            positions = self.preview_locator.get_shape_positions(index=i)
            rotations = self.preview_locator.get_shape_rotations(index=i)

            if positions:
                positions.reverse()
                self.preview_locator.set_shape_positions(index=i, positions=positions)
            if rotations:
                rotations.reverse()
                self.preview_locator.set_shape_rotations(index=i, rotations=rotations)

        self.reverse = reverse

        logger.debug(f'Reverse changed: {reverse}')

    def change_rotation_offset(self, rotation_offset: list[float]):
        """Change the rotation offset of the previewLocator.
        """
        if not self.preview_locator:
            return

        if not self.preview_locator.num_shapes:
            return

        if self.rotation_offset == rotation_offset:
            return

        invert_rotation_offset = lib_math.invert_rotation(self.rotation_offset)
        mult_rotation_offset = lib_math.mult_rotation([rotation_offset, invert_rotation_offset])

        for i in range(self.preview_locator.num_shapes):
            rotations = self.preview_locator.get_shape_rotations(index=i)

            if rotations:
                rotations = [lib_math.mult_rotation([mult_rotation_offset, rotation]) for rotation in rotations]
                self.preview_locator.set_shape_rotations(index=i, rotations=rotations)

        self.rotation_offset = rotation_offset

        logger.debug(f'Rotation offset changed: {rotation_offset}')

    def change_color(self, color: list[float]):
        """Change the color of the previewLocator.
        """
        if not self.preview_locator:
            return

        if not self.preview_locator.num_shapes:
            return

        if self.color == color:
            return

        for i in range(self.preview_locator.num_shapes):
            self.preview_locator.set_shape_color(index=i, color=color)

        self.color = color

        logger.debug(f'Color changed: {color}')

    def delete(self):
        """Delete the previewLocator.
        """
        if not self.preview_locator:
            logger.debug('No previewLocator to delete.')
            return

        try:
            transform = self.preview_locator.transform_name
            cmds.delete(transform)

            logger.debug(f'Preview deleted: {transform}')
        except Exception as e:
            logger.exception(e)


# Create transform nodes at selected object's position.

def bounding_box_center(*args, **kwargs) -> list[dict[str, list[float]]]:
    """Get the bounding box center of the selected object.

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    positions = __get_selected_positions()
    if not positions:
        logger.warning('No valid object selected.')
        return

    center_position = lib_math.get_bounding_box_center(positions[0])

    logger.debug(f'Bounding box center: {center_position}')

    return [{'position': [center_position], 'rotation': []}]


def gravity_center(*args, **kwargs) -> list[dict[str, list[float]]]:
    """Get the centroid of the selected object.

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    positions = __get_selected_positions()
    if not positions:
        logger.warning('No valid object selected.')
        return

    gravity_center_position = lib_math.get_centroid(positions[0])

    logger.debug(f'Gravity center: {gravity_center_position}')

    return [{'position': [gravity_center_position], 'rotation': []}]


def each_positions(*args, **kwargs) -> list[dict[str, list[float]]]:
    """Get the each position of the selected object.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and
    """
    include_rotation = kwargs.get('include_rotation', False)
    tangent_from_component = kwargs.get('tangent_from_component', False)

    positions = __get_selected_positions(include_rotation=include_rotation,
                                         tangent_from_component=tangent_from_component)
    if not positions:
        logger.warning('No valid object selected.')
        return

    logger.debug(f'Each positions: {positions}')

    return [{'position': positions[0], 'rotation': positions[1]}]


def closest_position(*args, **kwargs) -> list[dict[str, list[float]]]:
    """Get the closest point on the selected nurbs surface or curve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    include_rotation = kwargs.get('include_rotation', False)
    tangent_from_component = kwargs.get('tangent_from_component', False)

    positions = __get_selected_positions(only_component=True,
                                         include_rotation=include_rotation,
                                         closest_position=True,
                                         tangent_from_component=tangent_from_component)
    if not positions:
        logger.warning('No valid object selected.')
        return

    logger.debug(f'Closest positions: {positions}')

    return [{'position': positions[0], 'rotation': positions[1]}]


def inner_divide(*args, **kwargs) -> list[dict[str, list[float]]]:
    """Get the inner divided points of the selected object.

    Keyword Args:
        divisions (int): The number of divisions. Default is 1.
        include_rotation (bool): Whether to include rotation. Default is False.

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    transforms = cmds.ls(sl=True, type='transform')
    if not transforms:
        logger.warning('No valid object selected.')
        return

    if len(transforms) < 2:
        logger.warning('Select two or more objects.')
        return

    divisions = kwargs.get('divisions', 1)

    if divisions < 1:
        logger.warning('Invalid divisions.')
        return

    include_rotation = kwargs.get('include_rotation', False)

    reference_positions = [cmds.xform(transform, q=True, ws=True, t=True) for transform in transforms]
    if include_rotation:
        reference_rotations = [cmds.xform(transform, q=True, ws=True, ro=True) for transform in transforms]

    num_transforms = len(transforms)

    result_positions = []
    result_rotations = []
    for i in range(num_transforms - 1):
        positions = lib_math.inner_divide(reference_positions[i], reference_positions[i + 1], divisions)
        if i != (num_transforms - 2):
            positions.pop(-1)
        result_positions.extend(positions)

        if include_rotation:
            if i != (num_transforms - 2):
                result_rotations.extend([reference_rotations[i]] * divisions)
            else:
                result_rotations.extend([reference_rotations[i]] * (divisions + 1))

    logger.debug(f'Inner divided points: {result_positions}')

    return [{'position': result_positions, 'rotation': result_rotations}]


def __get_selected_positions(only_component: bool = False,
                             flatten_components: bool = False,
                             include_rotation: bool = False,
                             closest_position: bool = False,
                             tangent_from_component: bool = False) -> Optional[tuple[list[list[float]], list[list[float]]]]:
    """Get the selected object's position and rotation.

    Args:
        only_component (bool): Whether to get the component only. Default is False.
        include_rotation (bool): Whether to include rotation. Default is False.
        flatten_components (bool): Whether to flatten the mesh components. Default is False.
        closest_position (bool): Whether to get the closest position the nurbsSurface or curve. Default is False.
        tangent_from_component (bool): Whether to get the tangent from the component. Default is False.


    Returns:
        Optional[tuple[list[list[float]], list[list[float]]]: The position and rotation.
    """
    sel_transforms = cmds.ls(sl=True, type='transform')
    sel_components = cmds.filterExpand(sm=[28, 30, 31, 32, 34])

    if not sel_transforms and not sel_components:
        logger.warning('No valid object selected.')
        return

    result_positions = []
    result_rotations = []

    # Get the dagNode position and rotation
    if sel_transforms and not only_component:
        logger.debug(f'Dag nodes: {sel_transforms}')

        if include_rotation:
            for transform in sel_transforms:
                result_positions.append(cmds.xform(transform, q=True, ws=True, t=True))
                result_rotations.append(cmds.xform(transform, q=True, ws=True, ro=True))
        else:
            result_positions = [cmds.xform(transform, q=True, ws=True, t=True) for transform in sel_transforms]

        logger.debug(f'Transform positions: {result_positions}')
        logger.debug(f'Transform rotations: {result_rotations}')

    # Get the component position and rotation
    if sel_components:
        logger.debug(f'Component data: {sel_components}')

        component_positions = []
        component_rotations = []

        components_filter = lib_component.ComponentFilter(sel_components)

        # Mesh
        vertex_components = components_filter.get_vertex_components()
        edge_components = components_filter.get_edge_components()
        face_components = components_filter.get_face_components()

        # Flatten the mesh components
        if flatten_components and (face_components or edge_components):
            for shape, indices in face_components.items():
                mesh_conversion = lib_mesh.MeshConversion(shape)
                converted_indices = mesh_conversion.face_to_vertices(indices, flatten=True)
                if shape in vertex_components:
                    converted_indices[shape] = list(set(converted_indices + vertex_components[shape]))
                else:
                    vertex_components[shape] = converted_indices

            for shape, indices in edge_components.items():
                mesh_conversion = lib_mesh.MeshComponentConversion(shape)
                converted_indices = mesh_conversion.edge_to_vertices(indices, flatten=True)
                if shape in vertex_components:
                    converted_indices[shape] = list(set(converted_indices + vertex_components[shape]))
                else:
                    vertex_components[shape] = converted_indices

        # Vertex
        for shape, indices in vertex_components.items():
            mesh_vertex = lib_mesh.MeshVertex(shape)
            positions = mesh_vertex.get_vertex_positions(indices)
            component_positions.extend(positions)
            if include_rotation:
                normals = mesh_vertex.get_vertex_normals(indices)
                tangents = mesh_vertex.get_vertex_tangents(indices)

                if not tangent_from_component:
                    result_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                            for normal, tangent in zip(normals, tangents)])
                else:
                    connected_vertices_list = mesh_vertex.get_connected_vertices(indices)
                    for position, normal, tangent, connected_vertices in zip(positions, normals, tangents, connected_vertices_list):
                        connected_positions = mesh_vertex.get_vertex_positions(connected_vertices)

                        angle = math.pi

                        # If the number of connected vertices is even,
                        # select the one with the smallest angle between the vectors of the opposite vertices
                        num_connected = len(connected_vertices)
                        if num_connected % 2 == 0:
                            half_num_connected = num_connected // 2
                            for i in range(half_num_connected):
                                vector_tangent = connected_positions[i] - connected_positions[i + half_num_connected]
                                if vector_tangent * tangent < 0:
                                    vector_tangent *= -1.0
                                vector_angle = tangent.angle(vector_tangent)
                                if vector_angle < angle:
                                    angle = vector_angle
                                    result_tangent = vector_tangent
                        else:
                            # If the number of connected vertices is odd, select the one with the smallest angle to the vertex vector
                            for connected_position in connected_positions:
                                vector_tangent = connected_position - position
                                vector_angle = tangent.angle(vector_tangent)
                                if vector_angle < angle:
                                    angle = vector_angle
                                    result_tangent = vector_tangent

                        result_rotations.append(lib_math.vector_to_rotation(normal, result_tangent, primary_axis='z', secondary_axis='x'))

        # Edge
        for shape, indices in edge_components.items():
            mesh_edge = lib_mesh.MeshEdge(shape)
            component_positions.extend(mesh_edge.get_edge_position(indices))
            if include_rotation:
                normals = mesh_edge.get_edge_normal(indices)
                tangents = mesh_edge.get_edge_tangent(indices)

                if not tangent_from_component:
                    result_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                            for normal, tangent in zip(normals, tangents)])
                else:
                    # Get the vector of the vertices that make up the edge, which is closest to the current tangent
                    vertex_vectors = mesh_edge.get_edge_vector(indices, normalize=True)
                    for normal, tangent, vertex_vector in zip(normals, tangents, vertex_vectors):
                        tangent = lib_math.vector_orthogonalize(normal, tangent)
                        binormal = normal ^ tangent

                        result_tangent = None
                        angle = math.pi
                        for axis_vector, axis in zip([tangent, binormal], ['x', 'y']):
                            dot_product = axis_vector * vertex_vector
                            candidate_vector = dot_product > 0 and vertex_vector or vertex_vector * -1.0

                            vector_angle = axis_vector.angle(candidate_vector)
                            if vector_angle < angle:
                                angle = vector_angle
                                result_tangent = candidate_vector
                                tangent_axis = axis

                        result_rotations.append(lib_math.vector_to_rotation(normal, result_tangent,
                                                                            primary_axis='z', secondary_axis=tangent_axis))

        # Face
        for shape, indices in face_components.items():
            mesh_face = lib_mesh.MeshFace(shape)
            component_positions.extend(mesh_face.get_face_position(indices))
            if include_rotation:
                normals = mesh_face.get_face_normal(indices)
                tangents = mesh_face.get_face_tangent(indices)
                result_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                        for normal, tangent in zip(normals, tangents)])

        # NurbsCurve
        curve_cv_components = components_filter.get_curve_cv_components()
        curve_ep_components = components_filter.get_curve_ep_components()

        # CV
        for shape, indices in curve_cv_components.items():
            curve = lib_nurbsCurve.NurbsCurve(shape)
            positions = curve.get_cv_position(indices)
            if include_rotation or closest_position:
                closest_positions, params = curve.get_closest_positions(positions)
                if closest_position:
                    component_positions.extend(closest_positions)
                else:
                    component_positions.extend(positions)
            else:
                component_positions.extend(positions)

            if include_rotation:
                normals, tangents = curve.get_normal_and_tangents(params)
                component_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                            for normal, tangent in zip(normals, tangents)])

        # EP
        for shape, indices in curve_ep_components.items():
            curve = lib_nurbsCurve.NurbsCurve(shape)
            positions, params = curve.get_edit_position(indices)
            component_positions.extend(positions)
            if include_rotation:
                normals, tangents = curve.get_normal_and_tangents(params)
                component_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                            for normal, tangent in zip(normals, tangents)])

        # NurbsSurface
        surface_cv_components = components_filter.get_surface_cv_components()

        for shape, indices in surface_cv_components.items():
            surface = lib_nurbsSurface.NurbsSurface(shape)
            positions = surface.get_cv_position(indices)
            if include_rotation or closest_position:
                closest_positions, params = surface.get_closest_positions(positions)
                if closest_position:
                    component_positions.extend(closest_positions)
                else:
                    component_positions.extend(positions)
            else:
                component_positions.extend(positions)

            if include_rotation:
                normals, tangents = surface.get_normal_and_tangents(params)
                component_rotations.extend([lib_math.vector_to_rotation(normal, tangent, primary_axis='z', secondary_axis='x')
                                            for normal, tangent in zip(normals, tangents)])

        component_positions = lib_conversion.MPoint_to_float(component_positions)

        result_positions.extend(component_positions)
        result_rotations.extend(component_rotations)

        logger.debug(f'Bound positions: {result_positions}')
        logger.debug(f'Bound rotations: {result_rotations}')

    if not result_positions and not result_rotations:
        logger.warning('No valid position and rotation data.')
        return

    return result_positions, result_rotations


# Create transform nodes at on nurbsSurface or nurbsCurve.


def cv_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the cv positions of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        positions = curve_obj.get_cv_positions()
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, positions, **kwargs)

        positions = lib_conversion.MPoint_to_float(positions)
        result_data.append({'position': positions, 'rotation': rotations})

    logger.debug(f'CV positions: {result_data}')

    return result_data


def cv_closest_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the closest cv positions of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        positions = curve_obj.get_cv_positions()
        closest_positions, _ = curve_obj.get_closest_positions(positions)
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, closest_positions, **kwargs)

        closest_positions = lib_conversion.MPoint_to_float(closest_positions)
        result_data.append({'position': closest_positions, 'rotation': rotations})

    logger.debug(f'Closest CV positions: {result_data}')

    return result_data


def ep_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the ep positions of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        positions, _ = curve_obj.get_edit_positions()
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, positions, **kwargs)

        positions = lib_conversion.MPoint_to_float(positions)
        result_data.append({'position': positions, 'rotation': rotations})

    logger.debug(f'EP positions: {result_data}')

    return result_data


def length_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the positions from the length of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        length (float): The length of the curve. Default is 1.0.
        divisions (int): The number of divisions. Default is 1.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)
    divisions = kwargs.pop('divisions', 1)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        curve_positions_obj = lib_nurbsCurve.NurbsCurvePositions(curve_obj)
        positions, _ = curve_positions_obj.get_positions_length(num_divisions=divisions)
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, positions, **kwargs)

        positions = lib_conversion.MPoint_to_float(positions)
        result_data.append({'position': positions, 'rotation': rotations})

    logger.debug(f'Positions from length: {result_data}')

    return result_data


def param_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the positions from the parameter of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        divisions (int): The number of divisions. Default is 1.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)
    divisions = kwargs.pop('divisions', 1)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        curve_positions_obj = lib_nurbsCurve.NurbsCurvePositions(curve_obj)
        positions, _ = curve_positions_obj.get_positions_param(num_divisions=divisions)
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, positions, **kwargs)

        positions = lib_conversion.MPoint_to_float(positions)
        result_data.append({'position': positions, 'rotation': rotations})

    logger.debug(f'Positions from parameter: {result_data}')

    return result_data


def cloud_positions(*args, **kwargs) -> list[dict[str, list[list[float]]]]:
    """Get the positions from the cloud of the selected nurbsCurve.

    Keyword Args:
        include_rotation (bool): Whether to include rotation. Default is False.
        divisions (int): The number of divisions. Default is 1.
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Returns:
        list[{position: list[float], rotation: list[float]}]: The position and rotation.
    """
    curves = __get_selected_curves()
    if not curves:
        logger.warning('No valid nurbsCurve selected.')
        return

    include_rotation = kwargs.pop('include_rotation', False)
    divisions = kwargs.pop('divisions', 1)

    result_data = []
    for curve in curves:
        curve_obj = lib_nurbsCurve.NurbsCurve(curve)
        curve_positions_obj = lib_nurbsCurve.NurbsCurvePositions(curve_obj)
        positions, _ = curve_positions_obj.get_positions_cloud(num_divisions=divisions)
        rotations = []
        if include_rotation:
            rotations = __get_curve_rotations(curve, positions, **kwargs)

        positions = lib_conversion.MPoint_to_float(positions)
        result_data.append({'position': positions, 'rotation': rotations})

    logger.debug(f'Positions from cloud: {result_data}')

    return result_data


def __get_selected_curves() -> list[str]:
    """Get the selected nurbsCurve.

    Returns:
        list[str]: The selected nurbsCurve.
    """
    return cmds.ls(sl=True, dag=True, type='nurbsCurve', ni=True)


def __get_curve_rotations(curve: str, positions: list[om.MPoint], *args, **kwargs) -> list[list[float]]:
    """Get the curve rotations.

    Args:
        curve (str): The curve name.
        positions (list[list[float]]): The curve positions.

    Keyword Args:
        aim_vector_method (str): The aim vector method. Default is 'tangent'. 'tangent', 'next_point', 'previous_point'
        up_vector_method (str): The up vector method. Default is 'normal'. 'scene_up', 'normal', 'surface_normal'

    Notes:
        - If the up_vector_method is 'surface_normal', the curve must be on the surface.
        - If not found the surface, the up_vector_method will be 'normal'.

    Returns:
        list[list[float]]: The curve rotations.
    """
    aim_vector_method = kwargs.get('aim_vector_method', 'tangent')  # 'tangent', 'next_point', 'previous_point'
    up_vector_method = kwargs.get('up_vector_method', 'normal')  # 'scene_up', 'normal', 'surface_normal'

    if aim_vector_method not in ['tangent', 'next_point', 'previous_point']:
        raise ValueError('Invalid aim vector method.')

    if up_vector_method not in ['scene_up', 'normal', 'surface_normal']:
        raise ValueError('Invalid up vector method.')

    curve_obj = lib_nurbsCurve.NurbsCurve(curve)

    if up_vector_method == 'surface_normal':
        surface = None
        curve_iso = cmds.listConnections(f'{curve}.create', type='curveFromSurfaceIso')
        if not curve_iso:
            logger.warning('No valid curveFromSurfaceIso.')
        else:
            surface = cmds.listConnections(f'{curve_iso[0]}.inputSurface', type='nurbsSurface', shapes=True)

        if not surface:
            logger.warning('No valid nurbsSurface.')
            up_vector_method = 'normal'
        else:
            surface = lib_nurbsSurface.NurbsSurface(surface[0])
            iso_param = cmds.getAttr(f'{curve_iso[0]}.isoparmValue')
            iso_direction = cmds.getAttr(f'{curve_iso[0]}.isoparmDirection')

    num_positions = len(positions)

    rotations = []
    for i in range(num_positions):
        _, param = curve_obj.get_closest_position(positions[i])

        # Get the aim vector
        if aim_vector_method == 'tangent':
            aim_vector = curve_obj.get_tangent(param)
        elif aim_vector_method == 'next_point':
            if i == (num_positions - 1):
                aim_vector = positions[i] - positions[i - 1]
            else:
                aim_vector = positions[i + 1] - positions[i]
        elif aim_vector_method == 'previous_point':
            if i == 0:
                aim_vector = positions[i + 1] - positions[i]
            else:
                aim_vector = positions[i] - positions[i - 1]

        # Get the up vector
        if up_vector_method == 'scene_up':
            up_vector = [0.0, 1.0, 0.0]
        elif up_vector_method == 'normal':
            up_vector = curve_obj.get_normal(param)
        elif up_vector_method == 'surface_normal':
            params = iso_direction == 0 and [param, iso_param] or [iso_param, param]
            up_vector = surface.get_normal(params)

        # Get the rotation
        rotation = lib_math.vector_to_rotation(aim_vector, up_vector, primary_axis='z', secondary_axis='x')
        rotations.append(rotation)

    return rotations
