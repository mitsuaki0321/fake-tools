"""
Create a curve surface from nodes.
"""

from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds

from ..lib import (
    lib_math,
    lib_mesh,
    lib_nurbsCurve,
    lib_nurbsSurface,
    lib_selection,
    lib_skinCluster,
)
from . import convert_weight

logger = getLogger(__name__)


def main(
    select_type: str = "selected",
    object_type: str = "nurbsCurve",
    is_bind: bool = False,
    to_skin_cage: bool = False,
    skin_cage_division_levels: int = 1,
    select_options: dict = {},
    create_options: dict = {},
    bind_options: dict = {},
) -> list[str]:
    """Create and bind curve surface.

    Args:
        select_type (str): If "selected", get the selected nodes. If "hierarchy", get the hierarchy of the selected nodes.
        object_type (str): Type of object to create. 'nurbsCurve' or 'mesh' or 'nurbsSurface'.
        is_bind (bool): Whether to bind the created geometry.
        to_skin_cage (bool): Whether to bind to the skin cage. Only nurbsSurface is supported.
        skin_cage_division_levels (int): Number of division levels for the skin cage.
        select_options (dict): Options for selecting nodes.
        create_options (dict): Options for creating curve surface.
        bind_options (dict): Options for binding curve surface.

    Returns:
        list[str]: Created surface or curves.
    """
    sel_nodes = _get_selected_nodes(select_type, **select_options)

    result_objs = []
    for nodes in sel_nodes:
        create_curve_surface = CreateCurveSurface(nodes)
        obj = create_curve_surface.execute(object_type=object_type, **create_options)

        if not is_bind:
            result_objs.append(obj)
            continue

        if object_type == "nurbsCurve":
            _bind_curve_surface(nodes, obj)
            CurveWeightSetting(obj).execute(**bind_options)
            result_objs.append(obj)
        else:
            bind_curve = create_curve_surface.execute(object_type="nurbsCurve", **create_options)
            _bind_curve_surface(nodes, bind_curve)
            CurveWeightSetting(bind_curve).execute(**bind_options)

            _bind_curve_surface(nodes, obj)
            _transfer_curve_weights(bind_curve, obj)
            cmds.delete(bind_curve)

            if object_type == "nurbsSurface" and to_skin_cage:
                skin_cage = _to_skin_cage_from_length(obj, skin_cage_division_levels)
                cmds.delete(obj)

                result_objs.append(skin_cage)
            else:
                result_objs.append(obj)

    return result_objs


def _get_selected_nodes(select_type: str, skip: int = 0, reverse: bool = False) -> list[list[str]]:
    """Get selected nodes or hierarchy nodes.

    Args:
        select_type (str): If "selected", get the selected nodes. If "hierarchy", get the hierarchy of the selected nodes.
        skip (int): Value to skip selected nodes.
        reverse (bool): Whether to get the selected nodes in reverse order.

    Returns:
        list[list[str]]: Selected nodes.
    """
    sel_nodes = cmds.ls(sl=True, type="transform", l=True)
    if not sel_nodes:
        cmds.error("Select transform nodes.")

    node_list = []
    if select_type == "selected":
        node_list = [sel_nodes]
    elif select_type == "hierarchy":
        same_hierarchy = []
        for i in range(len(sel_nodes)):
            for j in range(len(sel_nodes)):
                if i == j:
                    continue

                if sel_nodes[i].startswith(sel_nodes[j]):
                    same_hierarchy.append(sel_nodes[i])
                    break

        if same_hierarchy:
            same_hierarchy = cmds.ls(same_hierarchy)
            cmds.error(f"Invalid hierarchy. Hierarchies are overlapping: {same_hierarchy}")

        for node in sel_nodes:
            node_list.append(lib_selection.DagHierarchy([node]).get_hierarchy(include_shape=False))

    if reverse:
        node_list = [list(reversed(nodes)) for nodes in node_list]

    if skip:
        skip += 1
        if all([skip < len(nodes) for nodes in node_list]):
            for i in range(len(node_list)):
                skip_nodes = node_list[i][::skip]
                if len(node_list[i]) % skip == 0:
                    skip_nodes.append(node_list[i][-1])

                node_list[i] = skip_nodes
        else:
            cmds.error("Invalid skip value.")

    logger.debug(f"Selected nodes: {node_list}")

    return node_list


def _bind_curve_surface(infs: list[str], obj: str) -> str:
    """Bind the influence nodes to the curve or surface or mesh.

    Args:
        infs (list[str]): Influence nodes.
        obj (str): Bind target geometry.

    Returns:
        str: SkinCluster node name.
    """
    if not infs:
        cmds.error("No influences specified.")

    if not obj:
        cmds.error("No geometry specified.")

    not_exist_infs = [inf for inf in infs if not cmds.objExists(inf)]
    if not_exist_infs:
        cmds.error(f"Influences not found: {not_exist_infs}")

    not_joint_infs = [inf for inf in infs if cmds.nodeType(inf) != "joint"]
    if not_joint_infs:
        cmds.error(f"Invalid influence type: {not_joint_infs}")

    shape = __validate_geometry(obj, ["nurbsCurve", "mesh", "nurbsSurface"])
    skinCluster = cmds.skinCluster(infs, shape, tsb=True)[0]

    logger.debug(f"Created skinCluster: {infs} -> {obj}")

    return skinCluster


def _transfer_curve_weights(curve: str, surface: str) -> None:
    """Transfer curve weights to the lofted surface or mesh.

    Args:
        curve (str): Curve shape name.
        surface (str): Target surface name.
    """
    if not curve:
        cmds.error("No curve specified.")

    if not surface:
        cmds.error("No target surface specified.")

    curve_shape = __validate_geometry(curve, "nurbsCurve")

    curve_skinCluster = lib_skinCluster.get_skinCluster(curve_shape)
    if not curve_skinCluster:
        cmds.error(f"No skinCluster found: {curve}")

    surface_shape = __validate_geometry(surface, ["nurbsSurface", "mesh"])

    surface_skinCluster = lib_skinCluster.get_skinCluster(surface_shape)
    if not surface_skinCluster:
        cmds.error(f"No skinCluster found: {surface}")

    surface_type = cmds.nodeType(surface_shape)
    weights = lib_skinCluster.get_skin_weights(curve_skinCluster, all_components=True)
    infs = cmds.skinCluster(curve_skinCluster, q=True, inf=True)
    num_cvs = len(weights)
    for i, weight in enumerate(weights):
        if surface_type == "nurbsSurface":
            cmds.skinPercent(surface_skinCluster, f"{surface}.cv[0][{i}]", transformValue=zip(infs, weight, strict=False))
            cmds.skinPercent(surface_skinCluster, f"{surface}.cv[1][{i}]", transformValue=zip(infs, weight, strict=False))
        elif surface_type == "mesh":
            cmds.skinPercent(surface_skinCluster, f"{surface}.vtx[{i}]", transformValue=zip(infs, weight, strict=False))
            cmds.skinPercent(surface_skinCluster, f"{surface}.vtx[{num_cvs + i}]", transformValue=zip(infs, weight, strict=False))

    logger.debug(f"Transfer weights: {curve} -> {surface}")


def _to_skin_cage_from_length(surface: str, division_levels: int = 1) -> str:
    """Convert the surface to skin cage.

    Args:
        surface (str): Surface name.
        division_levels (int): Number of division levels.

    Returns:
        str: Skin cage name.
    """
    if not surface:
        cmds.error("No surface specified.")

    if division_levels < 1:
        cmds.error("Invalid division levels.")

    surface_shape = __validate_geometry(surface, "nurbsSurface")

    skinCluster = lib_skinCluster.get_skinCluster(surface_shape)
    if not skinCluster:
        cmds.error(f"No skinCluster found: {surface_shape}")

    u_range, v_range = lib_nurbsSurface.NurbsSurface(surface_shape).get_uv_range()
    u_span, v_span = lib_nurbsSurface.NurbsSurface(surface_shape).get_uv_spans()
    u_value = (u_range[1] - u_range[0]) / 2.0
    v_value = (v_range[1] - v_range[0]) / 2.0

    u_curve = lib_nurbsSurface.create_curve_on_surface(f"{surface}.v[{v_value}]")
    v_curve = lib_nurbsSurface.create_curve_on_surface(f"{surface}.u[{u_value}]")

    u_curve_shape = cmds.listRelatives(u_curve, s=True, f=True, ni=True)[0]
    u_curve_length = lib_nurbsCurve.NurbsCurve(u_curve_shape).get_length()

    v_curve_shape = cmds.listRelatives(v_curve, s=True, f=True, ni=True)[0]
    v_curve_length = lib_nurbsCurve.NurbsCurve(v_curve_shape).get_length()

    u_divisions = int(lib_math.round_up(u_curve_length) / ((2 + u_span) / 4)) * division_levels
    v_divisions = int(lib_math.round_up(v_curve_length) / ((2 + v_span) / 4)) * division_levels

    skin_cage = convert_weight.SkinClusterToMesh(skinCluster, u_divisions=u_divisions, v_divisions=v_divisions).convert()

    cmds.delete(u_curve, v_curve)

    logger.debug(f"Created skin cage: {skin_cage}")

    return skin_cage


class CreateCurveSurface:
    """Create curve surface class.

    This class creates a curve and lofted surface and mesh from the specified nodes.
    """

    def __init__(self, nodes: list[str]):
        """Initialize the CreateCurveSurface class.

        Args:
            nodes (list[str]): Target nodes.
        """
        if not nodes:
            raise ValueError("No nodes specified.")

        not_exist_nodes = [node for node in nodes if not cmds.objExists(node)]
        if not_exist_nodes:
            raise ValueError(f"Nodes not found: {not_exist_nodes}")

        not_transform_nodes = [node for node in nodes if "transform" not in cmds.nodeType(node, inherited=True)]
        if not_transform_nodes:
            raise ValueError(f"Invalid node type: {not_transform_nodes}")

        self.nodes = nodes

    def execute(
        self,
        object_type: str = "nurbsCurve",
        degree: int = 3,
        center: bool = False,
        close: bool = False,
        divisions: int = 0,
        surface_width: float = 1.0,
        surface_width_center: float = 0.5,
        surface_axis: str = "x",
    ) -> str:
        """Create curve surface.

        Args:
            node_list (list[list[str]]): Target nodes.
            object_type (str): "nurbsCurve" or "mesh" or "nurbsSurface".
            degree (int): Degree of the curve.
            center (bool): Whether to create the curve at the center of the nodes.
            close (bool): Whether to close the curve.
            divisions (int): Number of CVs to insert between given positions.
            surface_width (float): Width of the surface.
            surface_width_center (float): Center point of the surface width. (0.0 to 1.0)
            surface_axis (str): Axis of the surface. ('x', 'y', 'z', 'normal', 'binormal')

        Returns:
            str: Created curve surface.
        """
        if object_type not in ["nurbsCurve", "mesh", "nurbsSurface"]:
            raise ValueError("Invalid object type.")

        if degree not in [1, 3]:
            raise ValueError("Invalid degree.")

        if object_type == "nurbsCurve":
            positions = [cmds.xform(node, q=True, ws=True, t=True) for node in self.nodes]
            return self._create_curve(positions, degree=degree, center=center, close=close, divisions=divisions)

        if surface_width < 0:
            raise ValueError("Invalid surface width.")

        if surface_width_center < 0 or surface_width_center > 1:
            raise ValueError("Invalid surface width point.")

        if surface_axis not in ["x", "y", "z", "normal", "binormal"]:
            raise ValueError("Invalid surface axis.")

        plus_point = surface_width * surface_width_center
        minus_point = plus_point - surface_width

        if surface_axis in ["normal", "binormal"]:
            node_positions = [cmds.xform(node, q=True, ws=True, t=True) for node in self.nodes]
            base_curve = self._create_curve(node_positions, degree=3, center=center, close=close, divisions=divisions)
            base_curve_shape = cmds.listRelatives(base_curve, s=True, f=True, ni=True)[0]
            base_nurbs_curve = lib_nurbsCurve.NurbsCurve(base_curve_shape)

        plus_positions = []
        minus_positions = []
        for node in self.nodes:
            matrix = om.MMatrix(cmds.xform(node, q=True, ws=True, m=True))
            position = om.MVector(cmds.xform(node, q=True, ws=True, t=True))

            if surface_axis == "x":
                minus_position = position + om.MVector(minus_point, 0, 0) * matrix
                plus_position = position + om.MVector(plus_point, 0, 0) * matrix
            elif surface_axis == "y":
                minus_position = position + om.MVector(0, minus_point, 0) * matrix
                plus_position = position + om.MVector(0, plus_point, 0) * matrix
            elif surface_axis == "z":
                minus_position = position + om.MVector(0, 0, minus_point) * matrix
                plus_position = position + om.MVector(0, 0, plus_point) * matrix
            elif surface_axis == "normal":
                _, param = base_nurbs_curve.get_closest_position(position)
                normal = base_nurbs_curve.get_normal(param).normal()
                minus_position = position + normal * minus_point
                plus_position = position + normal * plus_point
            elif surface_axis == "binormal":
                _, param = base_nurbs_curve.get_closest_position(position)
                normal = base_nurbs_curve.get_normal(param).normal()
                tangent = base_nurbs_curve.get_tangent(param).normal()
                binormal = normal ^ tangent
                minus_position = position + binormal * minus_point
                plus_position = position + binormal * plus_point

            minus_positions.append([minus_position.x, minus_position.y, minus_position.z])
            plus_positions.append([plus_position.x, plus_position.y, plus_position.z])

        plus_curve = self._create_curve(plus_positions, degree=degree, center=center, close=close, divisions=divisions)
        minus_curve = self._create_curve(minus_positions, degree=degree, center=center, close=close, divisions=divisions)

        surface = cmds.loft([plus_curve, minus_curve], ch=False, u=True, d=True)[0]
        cmds.delete(plus_curve, minus_curve)

        if object_type == "mesh":
            poly_surface = cmds.nurbsToPoly(surface, f=3, pt=1, ch=False)[0]
            cmds.delete(surface)

            logger.debug(f"Created mesh: {poly_surface}")

            return poly_surface

        logger.debug(f"Created surface: {surface}")

        return surface

    def _create_curve(self, positions: list[list[float]], degree: int = 3, center: bool = False, close: bool = False, divisions: int = 0) -> str:
        """Create curve from positions.

        Args:
            positions (list[float]): Target positions.
            degree (int): Degree of the curve.
            center (bool): Whether to create the curve at the center of the nodes.
            close (bool): Whether to close the curve.
            divisions (int): Number of CVs to insert between given positions.

        Returns:
            str: Created curve transform.
        """
        if degree not in [1, 3]:
            raise ValueError("Invalid degree.")

        num_positions = len(positions)
        if num_positions < 2:
            raise ValueError("At least two positions are required.")

        if num_positions == 2:
            if close:
                cmds.error("Cannot close the curve with only two positions.")

            if degree == 3:
                cmds.warning("Degree 3 curve requires at least 3 positions. Creating degree 1 curve instead.")

            curve = cmds.curve(d=1, p=positions)
            if divisions:
                curve_shape = cmds.listRelatives(curve, s=True, f=True)[0]
                lib_nurbsCurve.ConvertNurbsCurve(curve_shape).insert_cvs(divisions)

            return curve

        if num_positions == 3:
            curve = cmds.curve(d=1, p=positions)
            if degree == 3:
                curve = cmds.rebuildCurve(curve, ch=False, d=3, s=0)[0]
        else:
            curve = cmds.curve(d=degree, p=positions)

        if center or close or divisions:
            curve_shape = cmds.listRelatives(curve, s=True, f=True)[0]
            convert_nurbsCurve = lib_nurbsCurve.ConvertNurbsCurve(curve_shape)

            if close:
                convert_nurbsCurve.close_curve()

            if center and degree == 3:
                convert_nurbsCurve.center_curve()

            if divisions:
                convert_nurbsCurve.insert_cvs(divisions)

        logger.debug(f"Created curve: {curve}")

        return curve


class CurveWeightSetting:
    """Curve weight setting class.

    This class applies weights to a nurbsCurve.
    The method of applying weights is to set weights according to the length of the curve
    relative to the positions of the specified influences. (_calculate_weights)
    Then, you can specify whether to smooth the weights. (_smooth_weights)
    """

    def __init__(self, curve: str) -> None:
        """Initialize the CurveWeightSetting class.

        This method sets up the necessary attributes for applying weights to a nurbsCurve.

        Args:
            curve (str): Curve shape name.
        """
        if not curve:
            raise ValueError("Invalid curve name.")

        if not cmds.objExists(curve):
            raise ValueError(f"Curve not found: {curve}")

        curve_shape = cmds.listRelatives(curve, s=True, f=True, ni=True)
        if not curve_shape:
            raise ValueError(f"No shape found: {curve}")

        if cmds.nodeType(curve_shape[0]) != "nurbsCurve":
            raise ValueError(f"Invalid curve type: {curve}")

        skinCluster = lib_skinCluster.get_skinCluster(curve_shape[0])
        if not skinCluster:
            raise ValueError(f"No skinCluster found: {curve_shape[0]}")

        self.curve = curve
        self.nurbs_curve = lib_nurbsCurve.NurbsCurve(curve_shape[0])
        self.cv_positions = self.nurbs_curve.get_cv_positions()
        self.num_cvs = self.nurbs_curve.num_cvs
        self.is_closed = self.nurbs_curve.form != "open"
        self.total_length = self.nurbs_curve.get_length()

        self.skinCluster = skinCluster

    def execute(self, method="linear", smooth_iterations=10) -> None:
        """Weight interpolation on the curve.

        Args:
            method (str): Weight calculation method ('linear' or 'ease' or 'step').
            smooth_iterations (int): Number of smoothing iterations.
        """
        infs = cmds.skinCluster(self.skinCluster, q=True, inf=True)

        _, cv_params = self.nurbs_curve.get_closest_positions(self.cv_positions)
        cv_lengths = [self.nurbs_curve.fn.findLengthFromParam(cv_param) for cv_param in cv_params]

        inf_positions = [cmds.xform(inf, q=True, ws=True, t=True) for inf in infs]
        _, inf_params = self.nurbs_curve.get_closest_positions(inf_positions)
        inf_lengths = [self.nurbs_curve.fn.findLengthFromParam(inf_param) for inf_param in inf_params]

        sorted_infs, sorted_lengths = zip(*sorted(zip(infs, inf_lengths, strict=False), key=lambda x: x[1]), strict=False)

        cv_weights = self._calculate_weights(cv_lengths, sorted_lengths, method)

        if smooth_iterations:
            cv_weights = self._smooth_weights(cv_weights, smooth_iterations)

        cmds.skinCluster(self.skinCluster, e=True, normalizeWeights=0)
        for i in range(len(cv_lengths)):
            cmds.skinPercent(self.skinCluster, f"{self.curve}.cv[{i}]", transformValue=list(zip(sorted_infs, cv_weights[i], strict=False)))
        cmds.skinCluster(self.skinCluster, e=True, normalizeWeights=1)

    def _calculate_weights(self, cv_lengths, inf_lengths, method) -> list[list[float]]:
        """Calculate weights for each CV.

        Args:
            cv_lengths (list[float]): Lengths of CVs.
            inf_lengths (list[float]): Lengths of influences.
            method (str): Weight calculation method ('linear' or 'ease' or 'step').

        Returns:
            list[list[float]]: Weights for each CV.
        """
        if method not in ["linear", "ease", "step"]:
            raise ValueError(f"Invalid method '{method}'. Valid options are: 'linear', 'ease', 'step'.")

        cv_weights = []
        num_infs = len(inf_lengths)

        for i, cv_length in enumerate(cv_lengths):
            weights = [0.0] * num_infs

            out_of_range = True
            for j in range(num_infs - 1):
                if cv_length == inf_lengths[j]:
                    weights[j] = 1.0
                    out_of_range = False
                    break
                elif cv_length == inf_lengths[j + 1]:
                    weights[j + 1] = 1.0
                    out_of_range = False
                    break
                elif inf_lengths[j] < cv_length < inf_lengths[j + 1]:
                    t = (cv_length - inf_lengths[j]) / (inf_lengths[j + 1] - inf_lengths[j])
                    if method == "linear":
                        weights[j] = 1.0 - t
                        weights[j + 1] = t
                    elif method == "ease":
                        weights[j] = 1.0 - self.__ease_weight(t, ease_type="inout")
                        weights[j + 1] = self.__ease_weight(t, ease_type="inout")
                    elif method == "step":
                        weights[j] = 1.0

                    out_of_range = False
                    break

            if out_of_range:
                if self.is_closed:
                    numerator = cv_length > inf_lengths[-1] and cv_length - inf_lengths[-1] or cv_length + self.total_length - inf_lengths[-1]
                    denominator = (
                        inf_lengths[0] > inf_lengths[-1] and inf_lengths[0] - inf_lengths[-1] or inf_lengths[0] + self.total_length - inf_lengths[-1]
                    )
                    t = numerator / denominator
                    if method == "linear":
                        weights[-1] = 1.0 - t
                        weights[0] = t
                    elif method == "ease":
                        weights[-1] = 1.0 - self.__ease_weight(t, ease_type="inout")
                        weights[0] = self.__ease_weight(t, ease_type="inout")
                    elif method == "step":
                        weights[-1] = 1.0
                else:
                    if cv_length < inf_lengths[0]:
                        weights[0] = 1.0
                    elif cv_length > inf_lengths[-1]:
                        weights[-1] = 1.0

            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]

            cv_weights.append(weights)

        logger.debug(f"Calculated weights: {cv_weights}")

        return cv_weights

    def _smooth_weights(self, now_weights, iterations=10) -> list[list[float]]:
        """Smooth weights by blending with neighboring CV weights.

        Args:
            now_weights (list[list[float]]): Before smoothing weights.
            iterations (int): Number of smoothing iterations.

        Returns:
            list[list[float]]: Smoothed weights.
        """
        distances = []
        for i in range(self.num_cvs - 1):
            distances.append(self.cv_positions[i + 1].distanceTo(self.cv_positions[i]))

        num_infs = len(now_weights[0])

        neighbor_indices = []
        for i in range(self.num_cvs):
            if i == 0:
                if self.is_closed:
                    neighbor_indices.append([self.num_cvs - 1, i, i + 1])
                else:
                    neighbor_indices.append([])
            elif i == self.num_cvs - 1:
                if self.is_closed:
                    neighbor_indices.append([i - 1, i, 0])
                else:
                    neighbor_indices.append([])
            else:
                neighbor_indices.append([i - 1, i, i + 1])

        smooth_weights = [[0.0] * num_infs for _ in range(self.num_cvs)]
        for _ in range(iterations):
            for i in range(self.num_cvs):
                if not neighbor_indices[i]:
                    smooth_weights[i] = now_weights[i]
                    continue

                neighbor_weights = []
                neighbor_distances = []

                for index in neighbor_indices[i]:
                    neighbor_weights.append(now_weights[index])
                    if index < i:
                        neighbor_distances.append(distances[index])
                    elif index > i:
                        neighbor_distances.append(distances[i])
                    else:
                        neighbor_distances.append(1.0)

                total_distance = sum(1.0 / d for d in neighbor_distances)
                weighted_sum = [0.0] * num_infs

                for weight, dist in zip(neighbor_weights, neighbor_distances, strict=False):
                    for j in range(len(weight)):
                        weighted_sum[j] += weight[j] * (1.0 / dist)

                smooth_weights[i] = [w / total_distance for w in weighted_sum]

            now_weights = [w[:] for w in smooth_weights]

        logger.debug(f"Smoothed weights: {smooth_weights}")

        return smooth_weights

    @staticmethod
    def __ease_weight(t, ease_type="in") -> float:
        """Ease-In/Ease-Out weight calculation.

        Args:
            t (float): Normalized position (0 to 1).
            ease_type (str): 'in' for Ease-In, 'out' for Ease-Out, 'inout' for Ease-In-Out.

        Returns:
            float: Calculated ease weight.
        """
        if ease_type == "in":
            return t**2
        elif ease_type == "out":
            return 1 - (1 - t) ** 2
        elif ease_type == "inout":
            if t < 0.5:
                return 2 * (t**2)
            else:
                return 1 - 2 * ((1 - t) ** 2)

        raise ValueError("Invalid ease_type. Use 'in', 'out', or 'inout'.")


def __validate_geometry(geometry: str, node_types: list[str] = ["nurbsCurve"]) -> str:
    """Validate the geometry.

    Args:
        geometry (str): Geometry name.
        node_type (str): Type of node to validate.

    Returns:
        str: Validated geometry name.
    """
    if not geometry:
        cmds.error("No geometry specified.")

    if not cmds.objExists(geometry):
        cmds.error(f"Geometry not exists: {geometry}")

    shape = cmds.listRelatives(geometry, s=True, f=True, ni=True)
    if not shape:
        cmds.error(f"No shape found: {geometry}")

    if cmds.nodeType(shape[0]) not in node_types:
        cmds.error(f"Invalid geometry type: {shape[0]}")

    return shape[0]


def create_curve_from_vertices(target_vertices: list[str]) -> str:
    """Create a curve from the vertices.

    Args:
        target_vertices (list[str]): Target vertices.

    Returns:
        str: Created curve.
    """
    if not target_vertices or not isinstance(target_vertices, list):
        cmds.error("No vertices specified.")

    if not cmds.filterExpand(target_vertices, sm=31):
        cmds.error("No vertices found. Select vertices.")

    mesh = cmds.ls(target_vertices, objectsOnly=True)[0]
    mesh_vertex = lib_mesh.MeshVertex(mesh)
    num_vertices = mesh_vertex.num_vertices()
    all_positions = mesh_vertex.get_vertex_positions(as_float=True)

    target_vertices = cmds.ls(target_vertices, fl=True)
    if len(target_vertices) == num_vertices:
        cmds.error("All vertices are selected. Please select a subset of vertices.")
        return

    vertex_indices = mesh_vertex.get_vertex_indices(target_vertices)
    positions = [all_positions[i] for i in vertex_indices]
    center_position = lib_math.get_bounding_box_center(positions)

    mesh_conversion = lib_mesh.MeshComponentConversion(mesh)
    result_positions = [center_position]
    while True:
        face_indices = mesh_conversion.vertex_to_faces(vertex_indices, flatten=True)
        expanded_indices = mesh_conversion.face_to_vertices(face_indices, flatten=True)

        position_indices = list(set(expanded_indices) - set(vertex_indices))
        center_position = lib_math.get_bounding_box_center([all_positions[i] for i in position_indices])
        result_positions.append(center_position)

        if len(expanded_indices) >= num_vertices:
            break

        vertex_indices = expanded_indices

    curve = cmds.curve(d=1, p=result_positions)
    mesh_transform = cmds.listRelatives(mesh, p=True)[0]
    renamed_curve = cmds.rename(curve, f"{mesh_transform}_centerCurve")

    logger.debug(f"Created curve: {renamed_curve}")

    return renamed_curve


def move_cv_positions(target_cv: str) -> None:
    """Move CV positions of the curve.

    Args:
        target_cv (str): Target CVs.
    """
    if not target_cv:
        cmds.error("No cv specified.")

    if not cmds.filterExpand(target_cv, sm=28):
        cmds.error("No CVs found. Select CVs.")

    curve_shape = cmds.ls(target_cv, objectsOnly=True)[0]
    nurbs_curve = lib_nurbsCurve.NurbsCurve(curve_shape)
    if nurbs_curve.form == "open":
        cmds.error("Open curve is not supported.")

    cv_positions = nurbs_curve.get_cv_positions(as_float=True)

    cvs = cmds.ls(f"{curve_shape}.cv[*]", fl=True)
    target_cv = cmds.ls(target_cv, fl=True)[0]

    target_cv_index = cvs.index(target_cv)
    move_positions = cv_positions[target_cv_index:] + cv_positions[:target_cv_index]

    for cv, move_position in zip(cvs, move_positions, strict=False):
        cmds.xform(cv, ws=True, t=move_position)

    logger.debug(f"Moved CV positions: {target_cv}")


def create_curve_on_surface(suf: str, surface_axis: str = "u") -> str:
    """Create a center curve from the surface.

    Args:
        suf (str): Surface name.
        surface_axis (str): Axis of the surface. ('u' or 'v')

    Returns:
        str: Created curve.
    """
    if not suf:
        cmds.error("No surface specified.")

    if not cmds.objExists(suf):
        cmds.error(f"Surface not exists: {suf}")

    if cmds.nodeType(suf) != "nurbsSurface":
        cmds.error(f"Invalid surface type: {suf}")

    if surface_axis not in ["u", "v"]:
        cmds.error("Invalid surface axis.")

    nurbs_surface = lib_nurbsSurface.NurbsSurface(suf)
    u_range, v_range = nurbs_surface.get_uv_range()
    center_param = (u_range[0] + u_range[1]) / 2.0 if surface_axis == "u" else (v_range[0] + v_range[1]) / 2.0

    nodes = cmds.duplicateCurve(f"{suf}.{surface_axis == 'u' and 'v' or 'u'}[{center_param}]", ch=True, rn=False, local=False, n=f"{suf}_centerCurve")
    cmds.rename(nodes[1], f"{suf}_curveFromSurfaceIso")

    logger.debug(f"Created curve: {nodes[0]}")

    return nodes[0]
