"""
Mesh functions.
"""

from logging import getLogger
from typing import Optional

import maya.api.OpenMaya as om
import maya.cmds as cmds

logger = getLogger(__name__)


class MeshComponent:
    """Mesh component class.
    """

    def __init__(self, mesh: str):
        """Initialize the Mesh class.

        Args:
            mesh (str): The mesh name.
        """
        if not cmds.objExists(mesh):
            raise ValueError(f'Mesh does not exist: {mesh}')

        if not cmds.objectType(mesh) == 'mesh':
            raise ValueError(f'Not a mesh: {mesh}')

        selection_list = om.MSelectionList()
        selection_list.add(mesh)

        self._mesh_name = mesh
        self._dag_path = selection_list.getDagPath(0)
        self._mesh_fn = om.MFnMesh(self._dag_path)

    def get_mesh_name(self) -> str:
        """Get the mesh name.

        Returns:
            str: The mesh name.
        """
        return self._mesh_name

    def get_dag_path(self) -> om.MDagPath:
        """Get the DAG path.

        Returns:
            om.MDagPath: The DAG path.
        """
        return self._dag_path

    def get_mesh_fn(self) -> om.MFnMesh:
        """Get the mesh function set.

        Returns:
            om.MFnMesh: The mesh function set.
        """
        return self._mesh_fn

    def get_components_indices(self, components: list[str], component_type: str) -> list[int]:
        """Get the component indices.

        Args:
            components (list[str]): The component names
            component_type (str): The component type.

        Returns:
            list[int]: The component indices.
        """
        selection_list = om.MSelectionList()
        for component in components:
            selection_list.add(component)

        if selection_list.length() == 0:
            raise ValueError('No components found.')

        if selection_list.length() > 1:
            raise ValueError('Multiple components found.')

        component_path, component_obj = selection_list.getComponent(0)
        if component_obj.isNull():
            raise ValueError('Invalid component object.')

        component_type_str = {'face': 'kMeshPolygonComponent',
                              'edge': 'kMeshEdgeComponent',
                              'vertex': 'kMeshVertComponent'}

        if component_obj.apiTypeStr != component_type_str[component_type]:
            raise ValueError(f'Invalid component type: {component_obj.apiTypeStr}')

        if component_path != self._dag_path:
            raise ValueError('Component does not belong to the mesh')

        component_indices = om.MFnSingleIndexedComponent(component_obj).getElements()

        return list(component_indices)

    def get_components_from_indices(self, indices: list[int], component_type: str) -> list[str]:
        """Get the component names from the indices.

        Args:
            indices (list[int]): The component indices.
            component_type (str): The component type.

        Returns:
            list[str]: The component names.
        """
        if component_type not in ['face', 'edge', 'vertex']:
            raise ValueError(f'Invalid component type: {component_type}')

        mesh_transform = cmds.listRelatives(self._mesh_name, parent=True, path=True)[0]

        if component_type == 'face':
            num_faces = self._mesh_fn.numPolygons
            if min(indices) < 0 or max(indices) >= num_faces:
                raise ValueError('Face index out of range.')

            return [f'{mesh_transform}.f[{index}]' for index in indices]

        elif component_type == 'edge':
            num_edges = self._mesh_fn.numEdges
            if min(indices) < 0 or max(indices) >= num_edges:
                raise ValueError('Edge index out of range.')

            return [f'{mesh_transform}.e[{index}]' for index in indices]

        elif component_type == 'vertex':
            num_vertices = self._mesh_fn.numVertices
            if min(indices) < 0 or max(indices) >= num_vertices:
                raise ValueError('Vertex index out of range.')

            return [f'{mesh_transform}.vtx[{index}]' for index in indices]


class MeshVertex(MeshComponent):
    """Mesh vertex class.
    """

    def get_vertex_positions(self, vtx_indices: Optional[list[int]] = None) -> list[list[float]]:
        """Get the vertex positions.

        Args:
            vtx_indices (Optional[list[int]], optional): The vertex indices. Defaults to None. If None, get all vertex positions.

        Returns:
            list[om.MPoint]: The vertex positions.
        """
        if vtx_indices is None:
            positions = self._mesh_fn.getPoints(om.MSpace.kWorld)
        else:
            num_vertices = self._mesh_fn.numVertices
            for index in vtx_indices:
                if index >= num_vertices:
                    raise ValueError(f'Vertex index out of range: {index}')

            positions = [self._mesh_fn.getPoint(index, om.MSpace.kWorld) for index in vtx_indices]

        return positions

    def get_vertex_normals(self, vtx_indices: Optional[list[int]] = None) -> list[om.MVector]:
        """Get the vertex normals.

        Args:
            vtx_indices (Optional[list[int]], optional): The vertex indices. Defaults to None. If None, get all vertex normals.

        Returns:
            list[om.MVector]: The vertex normals.
        """
        if vtx_indices is None:
            normals = self._mesh_fn.getVertexNormals(False, om.MSpace.kWorld)
        else:
            num_vertices = self._mesh_fn.numVertices
            for index in vtx_indices:
                if index >= num_vertices:
                    raise ValueError(f'Vertex index out of range: {index}')

            normals = [self._mesh_fn.getVertexNormal(index, om.MSpace.kWorld) for index in vtx_indices]

        return normals

    def get_vertex_tangents(self, vtx_indices: Optional[list[int]] = None) -> list[om.MVector]:
        """Get the vertex tangents from the connected faces average.

        Args:
            vtx_indices (Optional[list[int]], optional): The vertex indices. Defaults to None. If None, get all vertex tangents.

        Returns:
            list[om.MVector]: The vertex tangents.
        """
        mit_vertex = om.MItMeshVertex(self._dag_path)
        num_vertices = self._mesh_fn.numVertices

        if vtx_indices is None:
            vtx_indices = range(num_vertices)

        result_tangents = []
        for index in vtx_indices:
            if index >= num_vertices:
                raise ValueError(f'Vertex index out of range: {index}')

            mit_vertex.setIndex(index)
            connected_face_ids = mit_vertex.getConnectedFaces()
            tangent = om.MVector(0.0, 0.0, 0.0)

            for face_id in connected_face_ids:
                try:
                    tangent += self._mesh_fn.getFaceVertexTangent(face_id, index, space=om.MSpace.kWorld)
                except RuntimeError:
                    logger.warning(f'Failed to get tangent for vertex: {index}')

            if len(connected_face_ids) > 1:
                tangent /= len(connected_face_ids)

            tangent.normalize()
            result_tangents.append(tangent)

        return result_tangents

    def get_vertex_binormals(self, vtx_indices: Optional[list[int]] = None) -> list[om.MVector]:
        """Get the vertex binormals from the connected faces average.

        Args:
            vtx_indices (Optional[list[int]], optional): The vertex indices. Defaults to None. If None, get all vertex binormals.

        Returns:
            list[om.MVector]: The vertex binormals.
        """
        mit_vertex = om.MItMeshVertex(self._dag_path)
        num_vertices = self._mesh_fn.numVertices

        if vtx_indices is None:
            vtx_indices = range(num_vertices)

        result_binormals = []
        for index in vtx_indices:
            if index >= num_vertices:
                raise ValueError(f'Vertex index out of range: {index}')

            mit_vertex.setIndex(index)
            connected_face_ids = mit_vertex.getConnectedFaces()
            binormal = om.MVector(0.0, 0.0, 0.0)

            for face_id in connected_face_ids:
                try:
                    binormal += self._mesh_fn.getFaceVertexBinormal(face_id, index, om.MSpace.kWorld)
                except RuntimeError:
                    logger.warning(f'Failed to get binormal for vertex: {index}')

            if len(connected_face_ids) > 1:
                binormal /= len(connected_face_ids)

            binormal.normalize()
            result_binormals.append(binormal)

        return result_binormals

    def get_vertex_shells(self) -> list[list[int]]:
        """Get the vertex shells.

        Returns:
            list[list[int]]: The vertex shells.
        """
        num_shells, shell_ids = self._mesh_fn.getMeshShellsIds(om.MFn.kMeshVertComponent)

        shells = [[] for _ in range(num_shells)]
        for vertex_id, shell_id in enumerate(shell_ids):
            shells[shell_id].append(vertex_id)

        return shells

    def get_connected_vertices(self, vtx_indices: list[int]) -> list[list[int]]:
        """Get the connected vertices.

        Args:
            vtx_indices (list[int]): The vertex indices.

        Returns:
            list[list[int]]: The connected vertices.
        """
        mit_vertex = om.MItMeshVertex(self._dag_path)
        num_vertices = self._mesh_fn.numVertices

        connected_vertices = []
        for index in vtx_indices:
            if index >= num_vertices:
                raise ValueError(f'Vertex index out of range: {index}')

            mit_vertex.setIndex(index)
            connected_vertices.append(list(mit_vertex.getConnectedVertices()))

        return connected_vertices

    def get_vertex_indices(self, components) -> list[int]:
        """Get the component indices.

        Args:
            components (list[str]): The component names.

        Returns:
            list[int]: The component indices.
        """
        return self.get_components_indices(components, 'vertex')

    def get_vertex_components(self, indices: list[int]) -> list[str]:
        """Get the component names from the indices.

        Args:
            indices (list[int]): The component indices.

        Returns:
            list[str]: The component names.
        """
        return self.get_components_from_indices(indices, 'vertex')

    def num_vertices(self) -> int:
        """Get the number of vertices.

        Returns:
            int: The number of vertices.
        """
        return self._mesh_fn.numVertices


class MeshFace(MeshComponent):
    """Mesh face class.
    """

    def get_face_position(self, face_ids: list[int]) -> list[om.MPoint]:
        """Get the face center position.

        Args:
            face_ids (list[int]): The face ids.

        Returns:
            list[om.MPoint]: The face positions.
        """
        num_faces = self._mesh_fn.numPolygons

        mit_poly = om.MItMeshPolygon(self._dag_path)

        points = []
        for face_id in face_ids:
            if face_id >= num_faces:
                logger.warning(f'Face id is invalid: {face_id}')
                continue

            mit_poly.setIndex(face_id)
            points.append(mit_poly.center(om.MSpace.kWorld))

        return points

    def get_face_normal(self, face_ids: list[int]) -> list[om.MVector]:
        """Get the face normal.

        Args:
            face_ids (list[int]): The face ids.

        Returns:
            list[om.MVector]: The face normals.
        """
        num_faces = self._mesh_fn.numPolygons

        normals = []
        for face_id in face_ids:
            if face_id >= num_faces:
                logger.warning(f'Invalid face id: {face_id}')
                continue

            normal = self._mesh_fn.getPolygonNormal(face_id, om.MSpace.kWorld)
            normals.append(normal)

        return normals

    def get_face_tangent(self, face_ids: list[int]) -> list[om.MVector]:
        """Get the face tangent.

        Args:
            face_ids (list[int]): The face ids.

        Returns:
            list[om.MVector]: The face tangents.
        """
        num_faces = self._mesh_fn.numPolygons

        mit_poly = om.MItMeshPolygon(self._dag_path)

        tangents = []
        for face_id in face_ids:
            if face_id >= num_faces:
                logger.warning(f'Invalid face id: {face_id}')
                continue

            mit_poly.setIndex(face_id)
            vertex_ids = mit_poly.getVertices()

            tangent = om.MVector(0.0, 0.0, 0.0)
            for vertex_id in vertex_ids:
                try:
                    tangent += self._mesh_fn.getFaceVertexTangent(face_id, vertex_id, om.MSpace.kWorld)
                except RuntimeError:
                    logger.warning(f'Failed to get tangent for face: {face_id}')

            tangent /= len(vertex_ids)
            tangent.normalize()

            tangents.append(tangent)

        return tangents

    def get_face_indices(self, components) -> list[int]:
        """Get the component indices.

        Args:
            components (list[str]): The component names.

        Returns:
            list[int]: The component indices.
        """
        return self.get_components_indices(components, 'face')

    def get_face_components(self, indices: list[int]) -> list[str]:
        """Get the component names from the indices.

        Args:
            indices (list[int]): The component indices.

        Returns:
            list[str]: The component names.
        """
        return self.get_components_from_indices(indices, 'face')

    def num_faces(self) -> int:
        """Get the number of faces.

        Returns:
            int: The number of faces.
        """
        return self._mesh_fn.numPolygons


class MeshEdge(MeshComponent):
    """Mesh edge class.
    """

    def get_edge_position(self, edge_ids: list[int]) -> list[om.MPoint]:
        """Get the edge center position.

        Args:
            edge_ids (list[int]): The edge ids.

        Returns:
            list[om.MPoint]: The edge positions.
        """
        num_edges = self._mesh_fn.numEdges

        mit_edge = om.MItMeshEdge(self._dag_path)

        points = []
        for edge_id in edge_ids:
            if edge_id >= num_edges:
                logger.warning(f'Invalid edge id: {edge_id}')
                continue

            mit_edge.setIndex(edge_id)
            points.append(mit_edge.center(om.MSpace.kWorld))

        return points

    def get_edge_normal(self, edge_ids: list[int]) -> list[om.MVector]:
        """Get the edge normal.

        Args:
            edge_ids (list[int]): The edge ids.

        Returns:
            list[om.MVector]: The edge normals.
        """
        num_edges = self._mesh_fn.numEdges

        normals = []
        for edge_id in edge_ids:
            if edge_id >= num_edges:
                continue

            edge_vertices = self._mesh_fn.getEdgeVertices(edge_id)
            vertex_normals = [self._mesh_fn.getVertexNormal(vertex_id, om.MSpace.kWorld) for vertex_id in edge_vertices]
            edge_normal = (vertex_normals[0] + vertex_normals[1]) / 2.0

            normals.append(edge_normal)

        return normals

    def get_edge_tangent(self, edge_ids: list[int]) -> list[om.MVector]:
        """Get the edge tangent.

        Args:
            edge_ids (list[int]): The edge ids.

        Returns:
            list[om.MVector]: The edge tangents.
        """
        num_edges = self._mesh_fn.numEdges

        mit_vertex = om.MItMeshVertex(self._dag_path)

        def __get_vertex_tangents(edge_vertices: list[int]) -> list[om.MVector]:
            """Get the vertex tangents.
            """
            result_tangents = []
            for index in edge_vertices:
                mit_vertex.setIndex(index)
                connected_face_ids = mit_vertex.getConnectedFaces()
                tangent = om.MVector(0.0, 0.0, 0.0)

                for face_id in connected_face_ids:
                    try:
                        tangent += self._mesh_fn.getFaceVertexTangent(face_id, index, om.MSpace.kWorld)
                    except RuntimeError:
                        logger.warning(f'Failed to get tangent for vertex: {index}')

                if len(connected_face_ids) > 1:
                    tangent /= len(connected_face_ids)

                tangent.normalize()
                result_tangents.append(tangent)

            return result_tangents

        tangents = []
        for edge_id in edge_ids:
            if edge_id >= num_edges:
                continue

            edge_vertices = self._mesh_fn.getEdgeVertices(edge_id)
            vertex_tangents = __get_vertex_tangents(edge_vertices)
            edge_tangent = (vertex_tangents[0] + vertex_tangents[1]) / 2.0

            tangents.append(edge_tangent)

        return tangents

    def get_edge_vector(self, edge_ids: list[int], normalize: bool = False) -> list[om.MVector]:
        """Get the vector between the two vertices that make up the edge.

        Args:
            edge_ids (list[int]): The edge ids.
            normalize (bool): Whether to normalize the vector. Default is False.

        Returns:
            list[om.MVector]: The edge vectors.
        """
        num_edges = self._mesh_fn.numEdges

        vectors = []
        for edge_id in edge_ids:
            if edge_id >= num_edges:
                continue

            edge_vertices = self._mesh_fn.getEdgeVertices(edge_id)
            vector = self._mesh_fn.getPoint(edge_vertices[1], om.MSpace.kWorld) - self._mesh_fn.getPoint(edge_vertices[0], om.MSpace.kWorld)

            if normalize:
                vector.normalize()

            vectors.append(vector)

        return vectors

    def get_edge_indices(self, components) -> list[int]:
        """Get the component indices.

        Args:
            components (list[str]): The component names.

        Returns:
            list[int]: The component indices.
        """
        return self.get_components_indices(components, 'edge')

    def get_edge_components(self, indices: list[int]) -> list[str]:
        """Get the component names from the indices.

        Args:
            indices (list[int]): The component indices.

        Returns:
            list[str]: The component names.
        """
        return self.get_components_from_indices(indices, 'edge')

    def num_edges(self) -> int:
        """Get the number of edges.

        Returns:
            int: The number of edges.
        """
        return self._mesh_fn.numEdges


class MeshPoint(MeshComponent):
    """Mesh point class.
    """

    def get_closest_points(self, reference_points: list[list[float]], max_distance: float = 100.0) -> list[om.MPointOnMesh]:
        """Get the closest point on the mesh.

        Args:
            reference_points (list[list[float]]): List of reference points.
            max_distance (float): The maximum distance. Default is 100.0.

        Returns:
            list[om.MPointOnMesh]: The closest points on the mesh.
        """
        mesh_intersector = om.MMeshIntersector()
        mesh_intersector.create(self._dag_path.node(), self._dag_path.inclusiveMatrix())

        result_data = []
        for reference_point in reference_points:
            reference_point = om.MPoint(reference_point)
            point_on_mesh = mesh_intersector.getClosestPoint(reference_point, max_distance)

            if point_on_mesh is None:
                logger.warning(f'No intersection found for point: {reference_point}')
                continue

            result_data.append(point_on_mesh)

        return result_data

    def get_intersect_point(self, start_point: list[float], end_point: list[float], **kwargs) -> Optional[tuple]:
        """Get the intersection point on the mesh.

        Args:
            start_point (list[float]): The start point.
            end_point (list[float]): The end point.

        Keyword Args:
            max_param (float): 	Specifies the maximum radius within which hits will be considered. Default is 1000.
            test_both_directions (bool): Specifies that hits in the negative rayDirection should also be considered. Default is False.

        Returns:
            tuple: The intersection data.(hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBay2)
        """
        max_param = kwargs.get('max_param', 1000)
        test_both_directions = kwargs.get('test_both_directions', False)

        start_point = om.MFloatPoint(start_point)
        end_point = om.MFloatPoint(end_point)
        ray_direction = end_point - start_point

        hit_data = self._mesh_fn.closestIntersection(start_point, ray_direction, om.MSpace.kWorld, max_param, test_both_directions)

        if hit_data is None:
            logger.warning(f'No intersection found for points: {start_point}, {end_point}, {self._mesh_name}')
            return None

        return hit_data


class MeshComponentConversion(MeshComponent):
    """Mesh component conversion class.
    """

    def face_to_vertices(self, face_ids: list[int], flatten: bool = False) -> list[list[int]]:
        """Convert the face ids to vertices.

        Args:
            face_ids (list[int]): The face ids.
            flatten (bool): Whether to flatten the vertices. Default is False.

        Returns:
            list[list[int]]: The vertices.
        """
        num_faces = self._mesh_fn.numPolygons

        vertices = []
        for face_id in face_ids:
            if face_id >= num_faces:
                logger.warning(f'Invalid face id: {face_id}')
                continue

            if flatten:
                vertex_ids = self._mesh_fn.getPolygonVertices(face_id)
                for vertex_id in vertex_ids:
                    if vertex_id not in vertices:
                        vertices.append(vertex_id)
            else:
                vertices.append(list(self._mesh_fn.getPolygonVertices(face_id)))

        return vertices

    def edge_to_vertices(self, edge_ids: list[int], flatten: bool = False) -> list[list[int]]:
        """Convert the edge ids to vertices.

        Args:
            edge_ids (list[int]): The edge ids.

        Returns:
            list[list[int]]: The vertices.
        """
        num_edges = self._mesh_fn.numEdges

        vertices = []
        for edge_id in edge_ids:
            if edge_id >= num_edges:
                logger.warning(f'Invalid edge id: {edge_id}')
                continue

            if flatten:
                vertex_ids = self._mesh_fn.getEdgeVertices(edge_id)
                for vertex_id in vertex_ids:
                    if vertex_id not in vertices:
                        vertices.append(vertex_id)
            else:
                vertices.append(list(self._mesh_fn.getEdgeVertices(edge_id)))

        return vertices

    def vertex_to_faces(self, vertex_ids: list[int], flatten: bool = False) -> list[list[int]]:
        """Convert the vertex ids to faces.

        Args:
            vertex_ids (list[int]): The vertex ids.
            flatten (bool): Whether to flatten the faces. Default is False.

        Returns:
            list[list[int]]: The faces.
        """
        mit_vertex = om.MItMeshVertex(self._dag_path)
        num_vertices = self._mesh_fn.numVertices

        faces = []
        for vertex_id in vertex_ids:
            if vertex_id >= num_vertices:
                logger.warning(f'Invalid vertex id: {vertex_id}')
                continue

            mit_vertex.setIndex(vertex_id)
            face_ids = mit_vertex.getConnectedFaces()
            if flatten:
                for face_id in face_ids:
                    if face_id not in faces:
                        faces.append(face_id)
            else:
                faces.append(list(face_ids))

        return faces


def is_same_topology(mesh_a: str, mesh_b: str) -> bool:
    """Check if two meshes have the same topology.

    Args:
        mesh_a (str): The first mesh.
        mesh_b (str): The second mesh.

    Returns:
        bool: True if the meshes have the same topology.
    """
    mesh_fn_a = MeshComponent(mesh_a).get_mesh_fn()
    mesh_fn_b = MeshComponent(mesh_b).get_mesh_fn()

    if mesh_fn_a.numVertices != mesh_fn_b.numVertices:
        logger.debug(f'Vertex count is different: {mesh_a}, {mesh_b}')
        return False

    if mesh_fn_a.numEdges != mesh_fn_b.numEdges:
        logger.debug(f'Edge count is different: {mesh_a}, {mesh_b}')
        return False

    if mesh_fn_a.numPolygons != mesh_fn_b.numPolygons:
        logger.debug(f'Face count is different: {mesh_a}, {mesh_b}')
        return False

    for i in range(mesh_fn_a.numPolygons):
        vertices_a = list(mesh_fn_a.getPolygonVertices(i))
        vertices_b = list(mesh_fn_b.getPolygonVertices(i))

        if vertices_a != vertices_b:
            logger.debug(f'The vertices that make up the face are different: {mesh_a}, {mesh_b} ({i})')
            return False

    return True
