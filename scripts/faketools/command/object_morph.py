"""Geometry and transform morphing commands.
"""

from __future__ import annotations

import math
import os
import pickle
from abc import ABC, abstractmethod
from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds
import numpy as np
from scipy.linalg import pinv
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

from ..lib import lib_name, lib_skinCluster, lib_transform

logger = getLogger(__name__)


class PositionBase(ABC):
    """Position base class.
    """

    @abstractmethod
    def export_data(self, positions: list[list[float]], **kwargs) -> dict:
        """Export the positions.

        Args:
            positions (list[list[float]]): The positions.

        Returns:
            dict: The exported data.
        """
        raise NotImplementedError('Method not implemented.')

    @abstractmethod
    def import_data(self, data: dict) -> list[list[float]]:
        """Import the data.

        Args:
            data (dict): The data.

        Returns:
            list[list[float]]: The imported positions.
        """
        raise NotImplementedError('Method not implemented.')


class DefaultPosition(PositionBase):
    """Default positions import/export class.

    A class that simply returns the input positions and rotations as they are.
    """

    def export_data(self, positions: list[list[float]], **kwargs) -> dict:
        """Export the positions.

        Args:
            positions (list[list[float]]): The positions.

        Keyword Args:
            rotations (list[list[float]]): The euler rotations. Default is [].

        Returns:
            dict: The exported data.
        """
        rotations = kwargs.get('rotations', [])
        return {'positions': positions, 'rotations': rotations}

    def import_data(self, data: dict) -> list[list[float]]:
        """Import the data.

        Args:
            data (dict): exported data.

        Returns:
            list[list[float]]: The imported positions.
        """
        if 'positions' not in data:
            raise ValueError('Missing positions data.')

        positions = data['positions']
        rotations = data.get('rotations', [])
        if rotations:
            if len(rotations) != len(positions):
                raise ValueError('Rotations and positions length mismatch.')

        return positions, rotations


class MeshPosition(PositionBase):
    """Mesh positions import/export base class.
    """

    def __init__(self, mesh: str):
        """Initialize the MeshPositions class.

        Args:
            mesh (str): The mesh name.
        """
        if not cmds.objExists(mesh):
            raise ValueError(f'Mesh does not exist: {mesh}')

        if cmds.objectType(mesh) != 'mesh':
            raise ValueError(f'Not a mesh: {mesh}')

        selection_list = om.MSelectionList()
        selection_list.add(mesh)

        self.mesh = mesh
        self.dag_path = selection_list.getDagPath(0)
        self.mesh_fn = om.MFnMesh(self.dag_path)


class MeshBaryPosition(MeshPosition):
    """Mesh positions import/export class using barycentric coordinates.
    """

    def __init__(self, target_mesh: str):
        """Initialize the MeshPositions class.

        Args:
            mesh (str): The mesh name.
        """
        super().__init__(target_mesh)

        self.mit_polygon = om.MItMeshPolygon(self.dag_path)

        self.mesh_intersector = om.MMeshIntersector()
        self.mesh_intersector.create(self.dag_path.node(), self.dag_path.inclusiveMatrix())

    def export_data(self, positions: list[list[float]], **kwargs) -> dict:
        """Export the positions to barycentric coordinates.

        Args:
            positions (list[list[float]]): The positions.

        Keyword Args:
            rotations (list[list[float]]): The euler rotations. Default is [].
            max_distance (float): The maximum distance. Default is 100.0.

        Returns:
            dict: The barycentric coordinates.
        """
        rotations = kwargs.get('rotations', [])
        if rotations:
            if len(rotations) != len(positions):
                raise ValueError('Rotations and positions length mismatch.')

        data = {}
        data['num_vertices'] = self.mesh_fn.numVertices

        weight_data = []
        for i, position in enumerate(positions):
            # Get the position data
            position = om.MPoint(position)
            point_on_mesh = self.mesh_intersector.getClosestPoint(position)

            u, v = point_on_mesh.barycentricCoords

            bary_data = {'weight': [u, v, 1.0 - u - v],
                         'face': point_on_mesh.face,
                         'triangle': point_on_mesh.triangle}

            normal = om.MVector(point_on_mesh.normal)

            self.mit_polygon.setIndex(point_on_mesh.face)
            points, _ = self.mit_polygon.getTriangle(point_on_mesh.triangle)
            tangent = points[0] - points[1]

            rot_matrix = self._get_rotation_matrix(normal, tangent)
            closest_to_pos_vector = position - om.MPoint(point_on_mesh.point)
            if closest_to_pos_vector.length() < 1e-10:
                bary_data['position'] = [0.0, 0.0, 0.0]
            else:
                rot_matrix_inv_pos = closest_to_pos_vector * rot_matrix.inverse()
                bary_data['position'] = [rot_matrix_inv_pos.x, rot_matrix_inv_pos.y, rot_matrix_inv_pos.z]

            # Get the rotation data
            if rotations:
                rotation = [math.radians(rot) for rot in rotations[i]]
                quat = om.MEulerRotation(rotation, om.MEulerRotation.kXYZ).asQuaternion()
                point_quat = om.MTransformationMatrix(rot_matrix).rotation(True)
                diff_quat = (quat * point_quat.inverse()).normal()
                bary_data['rotation'] = [diff_quat.x, diff_quat.y, diff_quat.z, diff_quat.w]

            weight_data.append(bary_data)

        data['weights'] = weight_data

        return data

    def import_data(self, data: dict) -> tuple[list[list[float]], list[list[float]]]:
        """Import the barycentric coordinates.

        Args:
            data (dict): The barycentric coordinates.

        Keyword Args:
            rotations (list[list[float]]): The euler rotations. Default is [].

        Returns:
            tuple[list[list[float]], list[list[float]]]: The positions and rotations
        """
        restored_positions = []
        restored_rotations = []

        weights = data.get('weights', [])

        for bary_data in weights:
            face_index = bary_data['face']
            triangle_index = bary_data['triangle']
            weight = bary_data['weight']

            try:
                self.mit_polygon.setIndex(face_index)
                points, _ = self.mit_polygon.getTriangle(triangle_index)
            except RuntimeError:
                raise ValueError(f"Invalid face index {face_index} or triangle index {triangle_index} in the current mesh.")

            # Calculate the restored position
            restored_position = points[0] * weight[0]
            restored_position += points[1] * weight[1]
            restored_position += points[2] * weight[2]

            # Adjust position using the stored offset and rotation matrix
            offset_vector = om.MVector(bary_data['position'])
            restored_position = om.MPoint(restored_position)
            point_on_mesh = self.mesh_intersector.getClosestPoint(restored_position)
            normal = om.MVector(point_on_mesh.normal)
            tangent = points[0] - points[1]
            rot_matrix = self._get_rotation_matrix(normal, tangent)
            restored_position += offset_vector * rot_matrix  # Rotate the offset vector

            restored_positions.append([restored_position.x, restored_position.y, restored_position.z])

            # Restore rotation if present
            rotation_data = bary_data.get('rotation')
            if rotation_data:
                rotation_quat = om.MQuaternion(rotation_data[0], rotation_data[1], rotation_data[2], rotation_data[3])
                rotation_quat = rotation_quat * om.MTransformationMatrix(rot_matrix).rotation(True)
                euler_rotation = rotation_quat.asEulerRotation()
                restored_rotations.append([math.degrees(euler_rotation.x), math.degrees(euler_rotation.y), math.degrees(euler_rotation.z)])
            else:
                logger.debug(f'No rotation data found for face: {face_index}, triangle: {triangle_index}')
                restored_rotations.append([0.0, 0.0, 0.0])

        return restored_positions, restored_rotations

    def _get_rotation_matrix(self, vector_a: om.MVector, vector_b: om.MVector) -> om.MQuaternion:
        """Get the rotation matrix.

        Args:
            vector_a (om.MVector): The first vector.
            vector_b (om.MVector): The second vector.

        Returns:
            om.MMatrix: The rotation matrix.
        """
        vector_a.normalize()
        vector_b.normalize()
        vector_b = (vector_b - (vector_a * vector_b) * vector_a).normal()
        cross_product_vector = vector_a ^ vector_b

        matrix = om.MMatrix([vector_a.x, vector_a.y, vector_a.z, 0.0,
                             vector_b.x, vector_b.y, vector_b.z, 0.0,
                             cross_product_vector.x, cross_product_vector.y, cross_product_vector.z, 0.0,
                             0.0, 0.0, 0.0, 1.0])

        return matrix


class MeshRBFPosition(MeshPosition):
    """Mesh positions import/export class using RBF.
    """

    _data_type = np.float32

    def export_data(self, positions: list[list[float]], method_instance: IndexQueryMethod, **kwargs) -> dict:
        """Export the positions to RBF-like interpolation.

        Args:
            positions (list[list[float]]): The positions.
            method_instance (IndexQueryMethod): The index query method instance.

        Raises:
            ValueError: If the mesh has less than 4 vertices.

        Returns:
            dict: The RBF-like interpolation.
        """
        if self.mesh_fn.numVertices < 4:
            raise ValueError('Mesh must have at least 4 vertices.')

        if method_instance is None:
            raise ValueError('Index query method instance not provided.')

        if not isinstance(method_instance, IndexQueryMethod):
            raise ValueError('Invalid index query method instance.')

        rotations = kwargs.get('rotations', [])
        rotation_positions = []
        if rotations:
            if len(rotations) != len(positions):
                raise ValueError('Rotations and positions length mismatch.')

            for position, rotation in zip(positions, rotations):
                quat = om.MEulerRotation([math.radians(rot) for rot in rotation], om.MEulerRotation.kXYZ).asQuaternion()
                quat_mat = quat.asMatrix()
                x_vector = om.MVector(om.MVector.kXaxisVector) * quat_mat
                y_vector = om.MVector(om.MVector.kYaxisVector) * quat_mat

                x_hit_distance = self._intersect_length(position, x_vector)
                y_hit_distance = self._intersect_length(position, y_vector)

                if x_hit_distance == 0.0 and y_hit_distance == 0.0:
                    vector_length = 1.0
                else:
                    vector_length = min(x_hit_distance, y_hit_distance)

                x_point = om.MPoint(position) + x_vector * vector_length
                y_point = om.MPoint(position) + y_vector * vector_length

                rotation_positions.append([[x_point.x, x_point.y, x_point.z], [y_point.x, y_point.y, y_point.z]])

        vtx_positions = self._get_vtx_positions()
        indices = method_instance.get_indices(vtx_positions, positions)

        # Add vertices if the number of elements in indices is less than 4
        index_counts = [len(index) for index in indices]
        if not all([count >= 4 for count in index_counts]):
            distance_index_query = DistanceIndexQuery(num_vertices=4)
            distance_indices = distance_index_query.get_indices(vtx_positions, positions)
            for i, count in enumerate(index_counts):
                if count < 4:
                    indices[i] = distance_indices[i]

        logger.debug(f'Exporting RBF-like interpolation with positions: {len(positions)}')

        return {'positions': positions,
                'vtx_positions': vtx_positions,
                'target_indices': indices,
                'rotation_positions': rotation_positions
                }

    def import_data(self, data: dict) -> list[list[float]]:
        """Import the RBF-like interpolation.

        Args:
            data (dict): The RBF-like interpolation.

        Returns:
            list[list[float]]: The positions.
        """
        if 'vtx_positions' not in data:
            raise ValueError('Missing vertex positions data.')

        trg_positions = data['positions']
        trg_indices_list = data['target_indices']
        src_positions_list = np.asarray(data['vtx_positions'])
        dst_positions_list = np.asarray(self._get_vtx_positions())

        print(f'trg_positions: {trg_positions}')
        print(f'trg_indices_list: {trg_indices_list}')

        trg_rotations_positions = data.get('rotation_positions', [])

        if len(src_positions_list) != len(dst_positions_list):
            raise ValueError(f'Source and destination positions length mismatch: src {len(src_positions_list)} != dest {len(dst_positions_list)}')

        computed_position_list = []
        computed_rotation_list = []
        for i in range(len(trg_positions)):
            src_positions = src_positions_list[trg_indices_list[i]]
            dst_positions = dst_positions_list[trg_indices_list[i]]

            if trg_rotations_positions:
                compute_positions = [trg_positions[i]] + trg_rotations_positions[i]
            else:
                compute_positions = [trg_positions[i]]

            mesh_mat = _rbf_base_matrix(src_positions, dataType=self._data_type)
            weight_point_x, weight_point_y, weight_point_z = _rbf_compute_weight(dst_positions, mesh_mat, dataType=self._data_type)
            computed_positions = _rbf_compute_points(src_positions, compute_positions, weight_point_x,
                                                     weight_point_y, weight_point_z, dataType=self._data_type)

            logger.debug(f'Computed positions: {computed_positions}')

            computed_position_list.append(computed_positions[0])

            if trg_rotations_positions:
                computed_rotation = self._vector_to_rotation(computed_positions[0], computed_positions[1], computed_positions[2])
                computed_rotation_list.append(computed_rotation)

        logger.debug(f'Imported RBF-like interpolation with positions: {len(trg_positions)}')

        return computed_position_list, computed_rotation_list

    def _get_vtx_positions(self) -> list[list[float]]:
        """Get the mesh positions.

        Returns:
            list[list[float]]: The mesh positions.
        """
        return [[point.x, point.y, point.z] for point in self.mesh_fn.getPoints(om.MSpace.kWorld)]

    def _vector_to_rotation(self, origin_point: list[float], x_point: list[float], y_point: list[float]) -> om.MQuaternion:
        """Convert the vectors to a euler rotation.
        Args:
            origin_point (list[float]): The origin point.
            x_point (list[float]): The x axis point.
            y_point (list[float]): The y axis point.

        Returns:
            list[float]: The euler rotation.
        """
        x_vector = om.MPoint(x_point) - om.MPoint(origin_point)
        y_vector = om.MPoint(y_point) - om.MPoint(origin_point)
        x_vector.normalize()
        y_vector.normalize()

        vector_ortho = (y_vector - (x_vector * y_vector) * x_vector).normal()

        z_vector = x_vector ^ vector_ortho

        matrix = om.MMatrix([x_vector.x, x_vector.y, x_vector.z, 0.0,
                             y_vector.x, y_vector.y, y_vector.z, 0.0,
                             z_vector.x, z_vector.y, z_vector.z, 0.0,
                             0.0, 0.0, 0.0, 1.0])

        rotation = om.MTransformationMatrix(matrix).rotation(asQuaternion=False)
        return [math.degrees(rot) for rot in rotation]

    def _intersect_length(self, origin_point: om.MPoint, direction_vector: om.MVector) -> float:
        """Get the intersection length.

        Args:
            origin_point (om.MPoint): The origin point.
            direction_vector (om.MVector): The direction vector.

        Returns:
            float: The intersection length.
        """
        ray_origin = om.MFloatPoint(origin_point)
        ray_direction = om.MFloatVector(direction_vector)

        hit_data = self.mesh_fn.closestIntersection(ray_origin, ray_direction, om.MSpace.kWorld, 100, False)

        if hit_data is None:
            return 0.0

        return hit_data[1]  # hitRayParam ( Parametric distance to the hit point along the ray. )


class IndexQueryMethod:

    def get_indices(self, mesh_points: list[list[float]], positions: list[list[float]]) -> list[list[int]]:
        raise NotImplementedError('Method not implemented.')


class DistanceIndexQuery(IndexQueryMethod):

    def __init__(self, num_vertices=10):
        """Initialize the DistanceIndexQuery class.

        Args:
            num_vertices (int): The number of vertices to return.
        """
        self.__num_vertices = num_vertices

    def get_indices(self, mesh_points: list[list[float]], positions: list[list[float]]) -> list[list[int]]:
        """Get the closest vertices to each specified position using a loop.

        Args:
            mesh_points (list[list[float]]): The mesh points.
            positions (list[list[float]]): The positions.

        Returns:
            list[list[int]]: The closest vertices for each position.
        """
        mesh_points = np.array(mesh_points)
        positions = np.array(positions)

        result_indices = []
        for position in positions:
            distances = np.linalg.norm(mesh_points - position, axis=1)
            closest_indices = np.argsort(distances)[:self.__num_vertices]

            result_indices.append(closest_indices.tolist())

        return result_indices


class RadiusIndexQuery(IndexQueryMethod):

    def __init__(self, radius: float = 1.0):
        """Initialize the RadiusIndexQuery class.

        Args:
            radius (float): The radius.
        """
        self.__radius = radius

    def get_indices(self, mesh_points: list[list[float]], positions: list[list[float]]) -> list[list[int]]:
        """Get the vertices within the radius for each position.

        Args:
            mesh_points (list[list[float]]): The target mesh points.
            positions (list[list[float]]): The radius center positions.

        Returns:
            list[list[int]]: The vertices within the radius for each position.
        """
        mesh_points = np.array(mesh_points)
        positions = np.array(positions)

        kd_tree = cKDTree(mesh_points)

        result_indices = []
        for position in positions:
            indices = kd_tree.query_ball_point(position, self.__radius)
            result_indices.append(indices)

        return result_indices


class NearestRadiusIndexQuery(IndexQueryMethod):

    def __init__(self, radius_multiplier=1.5):
        """Initialize the NearestRadiusIndexQuery class.

        Args:
            radius_multiplier (float): The radius multiplier.
        """
        self.__radius_multiplier = radius_multiplier

    def get_indices(self, mesh_points: list[list[float]], positions: list[list[float]]) -> list[list[int]]:
        """Get the vertices within the radius for each position.

        Args:
            mesh_points (list[list[float]]): The target mesh points.
            positions (list[list[float]]): The radius center positions.

        Returns:
            list[list[int]]: The vertices within the radius for each position.
        """
        mesh_points = np.array(mesh_points)
        positions = np.array(positions)

        kd_tree = cKDTree(mesh_points)
        result_indices = []
        for position in positions:
            dist, _ = kd_tree.query(position)
            effective_radius = self.__radius_multiplier * dist
            indices = kd_tree.query_ball_point(position, effective_radius)

            result_indices.append(indices)

        return result_indices


class SkinClusterIndexQuery(IndexQueryMethod):

    def __init__(self, mesh: str, max_vertices: int = 100):
        """Initialize the SkinClusterIndexQuery class.

        Args:
            mesh (str): The mesh name.
            max_vertices (int): The maximum vertices to consider. If 0, all vertices are considered.
        """
        if not cmds.objExists(mesh):
            raise ValueError(f'Mesh does not exist: {mesh}')

        if cmds.objectType(mesh) != 'mesh':
            raise ValueError(f'Not a mesh: {mesh}')

        self.__mesh = mesh
        self.__max_vertices = max_vertices

    def get_indices(self, mesh_points: list[list[float]], positions: list[list[float]]) -> list[list[int]]:
        """Get the closest vertices to each specified position using the skin cluster.

        Notes:
            - If max_vertices is not 0, get up to max_vertices vertices.


        Args:
            mesh_points (list[list[float]]): The mesh points.
            positions (list[list[float]]): The positions.

        Returns:
            list[list[int]]: The closest vertices for each position.
        """
        mesh_count = cmds.polyEvaluate(self.__mesh, vertex=True)
        if len(mesh_points) != mesh_count:
            raise cmds.error(f'Mesh vertex count mismatch: {len(mesh_points)} != {mesh_count}')

        temp_mesh = cmds.duplicate(self.__mesh, name=f'{self.__mesh}_temp')[0]
        temp_joints = []
        for i, pos in enumerate(positions):
            joint = cmds.createNode('joint', name=f'temp_joint_{i}', ss=True)
            cmds.xform(joint, ws=True, t=pos)
            temp_joints.append(joint)

        skin_cluster = cmds.skinCluster(temp_joints, temp_mesh, tsb=True, mi=1, nw=1)[0]
        skin_weights = np.asarray(lib_skinCluster.get_skin_weights(skin_cluster, all_components=True)).T
        if self.__max_vertices == 0:
            result_indices = [np.where(weights > 0.001)[0].tolist() for weights in skin_weights]
        else:
            mesh_points = np.array(mesh_points)
            result_indices = []
            for weights in skin_weights:
                weight_indices = np.where(weights > 0.001)[0]
                if weight_indices.size < self.__max_vertices:
                    result_indices.append(weight_indices.tolist())
                else:
                    distances = np.linalg.norm(mesh_points[weight_indices] - positions, axis=1)
                    closest_indices = weight_indices[np.argsort(distances)[:self.__max_vertices]]
                    result_indices.append(closest_indices.tolist())

        cmds.delete(temp_mesh)
        cmds.delete(temp_joints)

        return result_indices


def _rbf_base_matrix(rbf_input_points, dataType=np.float32):
    """Compute RBF Base Matrix with distance normalization.
    """
    mat_c = np.asarray(rbf_input_points, dtype=dataType)
    mat_cc = np.insert(mat_c, 3, 1., axis=1)

    mat_cct = mat_cc.transpose()
    A = mat_cct[..., :, np.newaxis]
    B = mat_cct[..., np.newaxis, :]
    mat_k = np.sqrt(((A - B)**2).sum(axis=0))

    mat_a = np.c_[mat_k, mat_cc]
    mat_a = np.r_[mat_a, np.c_[mat_cct, np.zeros([4, 4])]]

    return mat_a


def _rbf_compute_weight(compute_points: list[list[float]],
                        base_matrix: csr_matrix,
                        dataType: type = np.float32) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the RBF weights for the target points.

    Args:
        compute_points (list[list[float]]): Target points for which weights are computed.
        base_matrix (csr_matrix): The precomputed RBF matrix.
        dataType (type): Data type, default is np.float32.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: Arrays of weights for x, y, and z.
    """
    trg_x, trg_y, trg_z = np.asarray(compute_points, dtype=dataType).T
    trg_x = np.append(trg_x, [.0, .0, .0, .0])
    trg_y = np.append(trg_y, [.0, .0, .0, .0])
    trg_z = np.append(trg_z, [.0, .0, .0, .0])

    weights_x = _rbf_solve_weight(base_matrix, trg_x)
    weights_y = _rbf_solve_weight(base_matrix, trg_y)
    weights_z = _rbf_solve_weight(base_matrix, trg_z)

    return weights_x, weights_y, weights_z


def _rbf_solve_weight(base_matrix: csr_matrix,
                      trg_points: np.ndarray) -> np.ndarray:
    """Solve the system of linear equations for the RBF. Uses a sparse solver and falls back to pinv if necessary.

    Args:
        base_matrix (csr_matrix): The RBF base matrix.
        trg_points (np.ndarray): The extended target array for one axis.

    Returns:
        np.ndarray: The resulting weight array.
    """
    try:
        return spsolve(base_matrix, trg_points)
    except np.linalg.LinAlgError:
        logger.warning('Singular matrix detected. Using pinv instead.')
        return np.dot(pinv(base_matrix), trg_points)


def _rbf_compute_points(src_points: list[list[float]],
                        trg_points: list[list[float]],
                        weight_x: np.ndarray,
                        weight_y: np.ndarray,
                        weight_z: np.ndarray,
                        dataType: type = np.float32) -> list[tuple[float, float, float]]:
    """Generate final positions by applying the RBF weights to the source and target points.

    Args:
        src_points (list[list[float]]): The original source points.
        trg_points (list[list[float]]): The comparison or target points.
        weight_x (np.ndarray): Weights for x-axis.
        weight_y (np.ndarray): Weights for y-axis.
        weight_z (np.ndarray): Weights for z-axis.
        dataType (type): Data type, default is np.float32.

    Returns:
        list[tuple[float, float, float]]: The transformed (x, y, z) positions.
    """
    num_out = len(src_points)
    mat_c = np.asarray(src_points, dtype=dataType)

    mat_g = np.asarray(trg_points, dtype=dataType)
    mat_p = np.insert(mat_g, 3, 1., axis=1)

    out_x = np.dot(mat_p, weight_x[num_out:])
    out_y = np.dot(mat_p, weight_y[num_out:])
    out_z = np.dot(mat_p, weight_z[num_out:])

    A = mat_g
    B = mat_c
    AB = cdist(A, B, 'euclidean')

    out_x = np.dot(AB, weight_x[:num_out]) + out_x
    out_y = np.dot(AB, weight_y[:num_out]) + out_y
    out_z = np.dot(AB, weight_z[:num_out]) + out_z

    return [(float(px), float(py), float(pz)) for px, py, pz in zip(out_x, out_y, out_z)]


def export_transform_position(output_directory: str, file_name: str, method: str = 'barycentric', *args, **kwargs) -> None:
    """Export the transform positions to a file for GUI.

    Notes:
        - Exports the positions and rotations of the selected nodes.
        - The names of the selected nodes must be unique within the selection.

    Args:
        output_file_directory (str): The output file directory.
        file_name (str): The output file name.
        method (str): The method to use for exporting the positions. Default is 'barycentric'. Options are 'default', 'barycentric', 'rbf'.
    """
    # Validate output file path
    if not output_directory:
        cmds.error('Output file directory not provided.')

    if not file_name:
        cmds.error('Output file name not provided.')

    if not os.path.exists(output_directory):
        cmds.error(f'Output file directory not found: {output_directory}')

    output_file_path = os.path.join(output_directory, f'{file_name}.pkl')

    # Validate selection
    sel_nodes = cmds.ls(sl=True)

    if not sel_nodes:
        cmds.error('No nodes selected.')

    if method not in ['default', 'barycentric', 'rbf']:
        cmds.error('Please specify a valid method. Options are: default, barycentric, rbf')

    if method == 'default':
        not_transform_nodes = [node for node in sel_nodes if 'transform' not in cmds.nodeType(node, inherited=True)]
        if not_transform_nodes:
            cmds.error(f'Selected nodes are not transform nodes: {not_transform_nodes}')
        transforms = sel_nodes
    else:
        if len(sel_nodes) < 2:
            cmds.error('Please select at least two nodes. One mesh and one or more transform nodes.')

        not_transform_nodes = [node for node in sel_nodes if 'transform' not in cmds.nodeType(node, inherited=True)]
        if not_transform_nodes:
            cmds.error(f'Selected nodes are not transform nodes: {not_transform_nodes}')

        target_mesh_transform = sel_nodes[0]
        transforms = sel_nodes[1:]

        target_mesh = cmds.listRelatives(target_mesh_transform, s=True, ni=True, type='mesh')
        if not target_mesh:
            cmds.error(f'No mesh found in the first selected node: {target_mesh_transform}')

        target_mesh = target_mesh[0]

    # Check unique names in the selection
    local_names = [lib_name.get_local_name(transform) for transform in transforms]
    not_unique_names = [name for name in local_names if local_names.count(name) > 1]
    if not_unique_names:
        cmds.error(f'Selected nodes have non-unique names in selection: {not_unique_names}')

    # Get the positions and rotations
    positions = [cmds.xform(transform, q=True, ws=True, t=True) for transform in transforms]
    rotations = [cmds.xform(transform, q=True, ws=True, ro=True) for transform in transforms]

    if method == 'default':
        method_instance = DefaultPosition()
        position_data = method_instance.export_data(positions, rotations=rotations)
    else:
        if method == 'barycentric':
            method_instance = MeshBaryPosition(target_mesh)
            position_data = method_instance.export_data(positions, rotations=rotations)
        elif method == 'rbf':
            method_instance = MeshRBFPosition(target_mesh)
            index_query_method = NearestRadiusIndexQuery(radius_multiplier=1.5)
            position_data = method_instance.export_data(positions, rotations=rotations, method_instance=index_query_method)

    # Get the hierarchy data
    transform_hierarchy = lib_transform.TransformHierarchy()
    for transform in transforms:
        transform_hierarchy.register_node(transform)

    export_data = {'method': method, 'transforms': local_names, 'position_data': position_data,
                   'hierarchy_data': transform_hierarchy.get_hierarchy_data()}

    # Write the data to a file
    with open(output_file_path, 'wb') as f:
        pickle.dump(export_data, f)

    logger.debug(f'Exported transform positions: {output_file_path}')


def load_transform_position_data(input_file_path: str) -> dict:
    """Get the transform position data from a file.

    Args:
        input_file_path (str): The input file path.

    Returns:
        dict: The transform position data.
    """
    # Validate input file path
    if not input_file_path:
        cmds.error('Input file path not provided.')

    if not os.path.exists(input_file_path):
        cmds.error(f'Input file path not found: {input_file_path}')

    # Read the data
    with open(input_file_path, 'rb') as f:
        input_data = pickle.load(f)

    # Validate input data
    if 'method' not in input_data:
        cmds.error('Invalid input data. Missing method.')

    if 'transforms' not in input_data:
        cmds.error('Invalid input data. Missing transforms.')

    if 'position_data' not in input_data:
        cmds.error('Invalid input data. Missing position data.')

    return input_data


def _create_transform_node(name: str, object_type: str = 'transform', size: int = 1.0) -> str:
    """Create a new transform node.

    Args:
        name (str): The transform name.
        object_type (str): The creation object type. Default is 'transform'. Options are 'transform', 'locator', 'joint'.
        size (int): The creation node size. Default is 1.0.

    Returns:
        str: The new transform node name.
    """
    if object_type == 'transform':
        new_transform = cmds.createNode('transform', name=name, ss=True)
    elif object_type == 'locator':
        new_transform = cmds.spaceLocator(name=name)[0]
        cmds.setAttr(f'{new_transform}.localScale', size, size, size)
    elif object_type == 'joint':
        new_transform = cmds.createNode('joint', name=name, ss=True)
        cmds.setAttr(f'{new_transform}.radius', size)
    else:
        raise ValueError(f'Invalid creation node type: {object_type}')

    return new_transform


def import_transform_position(input_file_path: str, create_new: bool = False, is_rotation: bool = True, *args, **kwargs) -> None:
    """Import the transform positions from a file.

    Notes:
        - If the create_new flag is True, a new transform node is created and the data is set to that node.
        - If the create_new flag is False, the data is set to the selected node. The selected node must have a unique name in the scene.

    Args:
        input_file_path (str): The input file path.
        create_new (bool): Create new transform nodes. Default is False.
        is_rotation (bool): Import rotations. Default is True.

    Keyword Args:
        restore_hierarchy (bool): Restore the hierarchy only if create_new is True. Default is False.
        creation_object_type (str): The creation object type. Default is 'transform'. Options are 'transform', 'locator', 'joint'.
        creation_object_size (float): The creation object size. Default is 1.0.
    """
    restore_hierarchy = kwargs.get('restore_hierarchy', False)
    creation_object_type = kwargs.get('creation_object_type', 'transform')  # 'transform', 'locator', 'joint'
    creation_object_size = kwargs.get('creation_object_size', 1.0)

    # Read the data
    input_data = load_transform_position_data(input_file_path)

    method = input_data['method']
    target_transforms = input_data['transforms']
    position_data = input_data['position_data']
    hierarchy_data = input_data['hierarchy_data']

    # Get the target mesh
    if method in ['barycentric', 'rbf']:
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error('No mesh transform selected.')

        target_mesh_transform = sel_nodes[0]
        target_mesh = cmds.listRelatives(target_mesh_transform, s=True, ni=True, type='mesh')
        if not target_mesh:
            cmds.error(f'No mesh transform selected.: {target_mesh_transform}')

        target_mesh = target_mesh[0]

    # Check the target transforms
    if not create_new:
        not_exists_nodes = [node for node in target_transforms if not cmds.objExists(node)]
        if not_exists_nodes:
            cmds.error(f'Target transform node do not exist: {not_exists_nodes}')

        not_transform_nodes = [node for node in target_transforms if 'transform' not in cmds.nodeType(node, inherited=True)]
        if not_transform_nodes:
            cmds.error(f'Target transforms are not transform nodes: {not_transform_nodes}')

        not_unique_nodes = [transform for transform in target_transforms if not lib_transform.is_unique_node(transform)]
        if not_unique_nodes:
            cmds.error(f'Target transform nodes are not unique: {not_unique_nodes}')

    # Get the positions and rotations
    if method == 'default':
        method_instance = DefaultPosition()
        result_positions, result_rotations = method_instance.import_data(position_data)
    else:
        if method == 'barycentric':
            method_instance = MeshBaryPosition(target_mesh)
        elif method == 'rbf':
            method_instance = MeshRBFPosition(target_mesh)

        result_positions, result_rotations = method_instance.import_data(position_data)

    # Set the data to the transforms
    if create_new:
        new_transforms = []
        for i, transform in enumerate(target_transforms):
            new_transform = _create_transform_node(f'{transform}_position#', creation_object_type, creation_object_size)
            cmds.xform(new_transform, ws=True, t=result_positions[i])
            if is_rotation:
                cmds.xform(new_transform, ws=True, ro=result_rotations[i])
            new_transforms.append(new_transform)

        logger.debug(f'Created new transform nodes: {new_transforms}')

        if restore_hierarchy:
            transform_hierarchy = lib_transform.TransformHierarchy.set_hierarchy_data(hierarchy_data)
            for target_transform, new_transform in zip(target_transforms, new_transforms):
                register_parent = transform_hierarchy.get_registered_parent(target_transform)
                if not register_parent:
                    continue

                parent_transform = new_transforms[target_transforms.index(register_parent)]
                cmds.parent(new_transform, parent_transform)

            logger.debug(f'Restored transform hierarchy: {new_transforms}')

        cmds.select(new_transforms, r=True)
    else:
        reorder_transforms = lib_transform.reorder_transform_nodes(target_transforms)
        for i, transform in enumerate(reorder_transforms):
            index = target_transforms.index(transform)
            cmds.xform(transform, ws=True, t=result_positions[index])
            if is_rotation:
                cmds.xform(transform, ws=True, ro=result_rotations[index])

        cmds.select(reorder_transforms, r=True)

        logger.debug(f'Set transform positions: {reorder_transforms}')

    logger.debug(f'Imported transform positions: {input_file_path}')
