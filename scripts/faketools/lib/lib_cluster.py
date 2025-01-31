"""
Mesh vertex clustering functions.
"""

import random
from abc import ABC, abstractmethod
from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds
import numpy as np
from sklearn.cluster import DBSCAN, KMeans

logger = getLogger(__name__)


class Clustering(ABC):
    """Clustering class for mesh vertices.
    """

    def __init__(self, mesh: str):
        """Initialize the Cluster with a target mesh.

        Args:
          mesh (str): The target mesh.
        """
        if not mesh:
            raise ValueError('Mesh is not specified.')

        if not isinstance(mesh, str):
            raise ValueError('Mesh must be a string.')

        if not cmds.objExists(mesh):
            raise ValueError(f'Mesh does not exist: {mesh}')

        if 'mesh' not in cmds.nodeType(mesh, inherited=True):
            raise ValueError(f'Node is not a mesh: {mesh}')

        self.mesh = mesh

        sel_list = om.MSelectionList()
        sel_list.add(mesh)
        self.dag_path = sel_list.getDagPath(0)
        self.mesh_fn = om.MFnMesh(self.dag_path)

    @abstractmethod
    def get_clusters(self, *args, **kwargs) -> list[list[str]]:
        """Get the clusters of vertices.

        Returns:
            list[list[str]]: The list of cluster vertices.
        """
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}({self.mesh})'

    def __str__(self):
        return f'{self.__class__.__name__}({self.mesh})'


class SplitAxisClustering(Clustering):
    """Split axis clustering for mesh vertices.
    """

    def get_clusters(self, split_num: int, axis: str = 'x') -> list[list[int]]:
        """Get the clusters of vertices by splitting the mesh along an axis.

        Args:
            split_num (int): The number of splits.
            axis (str, optional): The axis to split. Defaults to 'x'.

        Returns:
            list[list[int]]: The list of vertex indices for each cluster.
        """
        if axis not in ['x', 'y', 'z']:
            raise ValueError(f'Invalid axis: {axis}')

        axis_idx = ['x', 'y', 'z'].index(axis)

        if split_num < 2:
            raise ValueError(f'Invalid split number: {split_num}')

        points = self.mesh_fn.getPoints(om.MSpace.kWorld)
        points = np.asarray(points).transpose()
        indices_sorted = np.argsort(points)
        split_array = np.array_split(indices_sorted[axis_idx], split_num)

        logger.debug(f"Split {len(points)} vertices into {split_num} clusters along the {axis} axis.")

        return split_array.tolist()


class KMeansClustering(Clustering):
    """K-means clustering for mesh vertices.
    """

    def get_clusters(self, n_clusters: int) -> list[list[str]]:
        """Apply K-means clustering to classify vertices.

        Features:
            - Calculate the centroid (mean) of each cluster and classify the vertices closest to that position into the cluster.
            - The number of clusters must be specified.
            - Classify all vertices into clusters.

        Args:
            n_clusters (int): The number of clusters.

        Returns:
            List[List[str]]: The list of vertices for each cluster.
        """
        if n_clusters < 1:
            raise ValueError("n_clusters must be greater than 0.")

        vertex_positions = np.array(self.mesh_fn.getPoints(om.MSpace.kWorld))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(vertex_positions)

        clusters = [[] for _ in range(n_clusters)]
        for i, label in enumerate(labels):
            clusters[label].append(i)

        logger.debug(f"Clustered {len(vertex_positions)} vertices into {n_clusters} clusters.")

        return clusters


class DBSCANClustering(Clustering):
    """DBSCAN clustering for mesh vertices.
    """

    def get_clusters(self, eps: float = 0.5, min_samples: int = 5) -> list[list[int]]:
        """Classify vertices using DBSCAN clustering and create a list for each cluster.

        Features:
            - Create clusters based on the distance defined by eps.
            - A cluster is formed by points with at least min_samples.
            - Not all vertices are classified into clusters.

        Args:
            eps (float): The maximum distance between points to be considered as a cluster (clustering range).
            min_samples (int): The minimum number of points to be considered as a cluster.

        Returns:
            list[list[int]]: The list of vertices for each cluster.
        """
        vertex_positions = np.array(self.mesh_fn.getPoints(om.MSpace.kWorld))

        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(vertex_positions)

        unique_labels = set(labels)
        unique_labels.discard(-1)

        clusters = [[] for _ in unique_labels]
        for i, label in enumerate(labels):
            if label != -1:
                clusters[label].append(i)

        logger.debug(f"Clustered {len(vertex_positions)} vertices into {len(unique_labels)} clusters.")

        return clusters


def cluster_vertex_colors(obj: str, cluster_indices: list[list[int]]) -> None:
    """Cluster the vertices and assign a color to each cluster.

    Args:
        obj (str): The target object.
        cluster_indices (list[list[int]]): The list of vertex indices for each cluster.
    """
    if not cmds.objExists(obj):
        raise ValueError(f'Object does not exist: {obj}')

    for cluster in cluster_indices:
        cluster_color = [random.uniform(0, 1) for _ in range(3)]

        vertices = [f'{obj}.vtx[{i}]' for i in cluster]
        cmds.polyColorPerVertex(vertices, rgb=cluster_color)

        logger.debug(f'Assigned color to cluster: {vertices}')
