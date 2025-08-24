"""
NurbsCurve and NurbsSurface functions.
"""

from logging import getLogger
from typing import Union

import maya.api.OpenMaya as om
import maya.cmds as cmds
from scipy.optimize import brentq

logger = getLogger(__name__)


class NurbsCurve:
    """NurbsCurve class."""

    def __init__(self, curve: str):
        """Initialize the NurbsCurve class.

        Args:
            curve (str): The curve name.
        """
        if not cmds.objExists(curve):
            raise ValueError(f"Node does not exist: {curve}")

        if cmds.nodeType(curve) != "nurbsCurve":
            raise ValueError(f"Invalid type: {curve}")

        selection_list = om.MSelectionList()
        selection_list.add(curve)

        self.curve = curve
        self.dag_path = selection_list.getDagPath(0)
        self.fn = om.MFnNurbsCurve(self.dag_path)

    @property
    def num_cvs(self):
        """Get the cv num.

        Returns:
            int: The cv num.
        """
        if self.fn.form != om.MFnNurbsCurve.kPeriodic:
            return self.fn.numCVs
        else:
            return self.fn.numCVs - self.fn.degree

    @property
    def num_spans(self):
        """Get the span num.

        Returns:
            int: The span num.
        """
        return self.fn.numSpans

    @property
    def form(self) -> str:
        """Get the form.

        Returns:
            str: The form. ('open', 'closed', 'periodic')
        """
        form_map = {
            om.MFnNurbsCurve.kOpen: "open",
            om.MFnNurbsCurve.kClosed: "closed",
            om.MFnNurbsCurve.kPeriodic: "periodic",
        }

        return form_map[self.fn.form]

    @property
    def degree(self):
        """Get the degree.

        Returns:
            int: The degree.
        """
        return self.fn.degree

    def get_length(self):
        """Get the length.

        Returns:
            float: The length.
        """
        return self.fn.length()

    def get_cv_position(self, cv_ids: list[int], as_float: bool = False) -> list[om.MPoint] | list[list[float]]:
        """Get the CV positions.

        Args:
            cv_ids (list[int]): The CV IDs.
            as_float (bool): Return as float. Default is False.

        Returns:
            Union[list[om.MPoint], list[list[float]]]: The positions.
        """
        positions = [self.fn.cvPosition(cv_id, om.MSpace.kWorld) for cv_id in cv_ids]
        if as_float:
            return [[pos.x, pos.y, pos.z] for pos in positions]

        return positions

    def get_cv_positions(self, as_float: bool = False) -> list[om.MPoint] | list[list[float]]:
        """Get the CV positions.

        Args:
            as_float (bool): Return as float. Default is False.

        Returns:
            Union[list[om.MPoint], list[list[float]]]: The positions.
        """
        cv_positions = list(self.fn.cvPositions(om.MSpace.kWorld))
        # Keeping the reference to the MPointArray pointer can cause errors in subsequent processing.
        cv_positions = [om.MPoint([pos.x, pos.y, pos.z]) for pos in cv_positions]

        if self.form == "periodic":
            return cv_positions[: -self.fn.degree]

        if as_float:
            return [[pos.x, pos.y, pos.z] for pos in cv_positions]

        return cv_positions

    def get_edit_position(self, edit_ids: list[int], as_float: bool = False) -> tuple[list[om.MPoint] | list[list[float]], list[float]]:
        """Get the edit points.

        Args:
            edit_ids (list[int]): The edit IDs.
            as_float (bool): Return as float. Default is False.

        Returns:
            tuple[Union[list[om.MPoint], list[list[float]]], list[float]]: The positions and parameters.
        """
        min_param, max_param = self.fn.knotDomain
        param_range = max_param - min_param

        positions = []
        params = []
        for edit_id in edit_ids:
            if edit_id < 0 or edit_id > self.fn.numSpans:
                raise ValueError("Edit ID is out of valid range.")

            param = min_param + edit_id * param_range / self.fn.numSpans
            position = self.fn.getPointAtParam(param, space=om.MSpace.kWorld)

            params.append(param)
            positions.append(position)

        if as_float:
            return [[pos.x, pos.y, pos.z] for pos in positions], params

        return positions, params

    def get_edit_positions(self, as_float: bool = False) -> tuple[list[om.MPoint] | list[list[float]], list[float]]:
        """Get the edit points.

        Args:
            as_float (bool): Return as float. Default is False.

        Returns:
            tuple[Union[list[om.MPoint], list[list[float]]], list[float]]: The positions and parameters.
        """
        min_param, max_param = self.fn.knotDomain
        param_range = max_param - min_param

        positions = []
        params = []
        for i in range(self.fn.numSpans + 1):
            param = min_param + i * param_range / self.fn.numSpans
            position = self.fn.getPointAtParam(param, space=om.MSpace.kWorld)

            params.append(param)
            positions.append(position)

        if as_float:
            return [[pos.x, pos.y, pos.z] for pos in positions], params

        return positions, params

    def get_closest_position(self, reference_position: list[float], as_float: bool = False) -> tuple[om.MPoint | list[float], float]:
        """Get the closest CV position.

        Args:
            reference_position (list[float]): The reference point.
            as_float (bool): Return as float. Default is False.

        Returns:
            tuple[Union[om.MPoint, list[float]], float]: The position and parameter.
        """
        closest_position, param = self.fn.closestPoint(om.MPoint(reference_position), space=om.MSpace.kWorld)

        if as_float:
            return [closest_position.x, closest_position.y, closest_position.z], param

        return closest_position, param

    def get_closest_positions(
        self, reference_positions: list[list[float]], as_float: bool = False
    ) -> tuple[Union[om.MPoint, list[float]], list[float]]:  # noqa
        """Get the closest CV positions.

        Args:
            reference_positions (list[list[float]]): The reference points.
            as_float (bool): Return as float. Default is False.

        Returns:
            tuple[Union[om.MPoint, list[float]], list[float]]: The positions and parameters.
        """
        positions = []
        params = []
        for reference_position in reference_positions:
            closest_position, param = self.fn.closestPoint(om.MPoint(reference_position), space=om.MSpace.kWorld)
            positions.append(closest_position)
            params.append(param)

        if as_float:
            return [[pos.x, pos.y, pos.z] for pos in positions], params

        return positions, params

    def get_normal(self, param: float) -> om.MVector:
        """Get the normal.

        Args:
            param (float): The parameter.

        Returns:
            list[om.MVector]: The normal.
        """
        return self.fn.normal(param, space=om.MSpace.kWorld)

    def get_tangent(self, param: float) -> om.MVector:
        """Get the tangent.

        Args:
            param (float): The parameter.

        Returns:
            om.MVector: The tangent.
        """
        return self.fn.tangent(param, space=om.MSpace.kWorld)

    def get_normal_and_tangents(self, params: list[float]) -> tuple[list[om.MVector], list[om.MVector]]:  # noqa
        """Get the normal and tangent.

        Args:
            params (list[float]): The parameters.

        Returns:
            tuple[list[om.MVector], list[om.MVector]]: The normals and tangents.
        """
        normals = []
        tangents = []
        for param in params:
            normal = self.fn.normal(param, space=om.MSpace.kWorld)
            tangent = self.fn.tangent(param, space=om.MSpace.kWorld)
            normals.append(normal)
            tangents.append(tangent)

        return normals, tangents

    def find_cloud_length_from_param(self, start_param: float, target_length: float, **kwargs) -> float:
        """Find the parameter where the chord length from the specified parameter equals the target length.

        Args:
            start_param (float): The starting parameter value.
            target_length (float): The target chord length.

        Keyword Args:
            max_iterations (int): Maximum number of iterations. Default is 100.
            tolerance (float): Tolerance. Default is 1e-5.

        Raises:
            ValueError: If a parameter corresponding to the target chord length cannot be found.

        Returns:
            float: The parameter value corresponding to the target chord length.
        """
        max_iterations = kwargs.get("max_iterations", 100)
        tolerance = kwargs.get("tolerance", 1e-5)

        min_param, max_param = self.fn.knotDomain

        if not min_param <= start_param < max_param:
            raise ValueError("start_param is out of valid range.")

        start_point = self.fn.getPointAtParam(start_param, space=om.MSpace.kWorld)

        def chord_length_func(param):
            if param > max_param:
                return target_length
            point = self.fn.getPointAtParam(param, space=om.MSpace.kWorld)
            return start_point.distanceTo(point) - target_length

        try:
            end_param = brentq(chord_length_func, start_param, max_param, xtol=tolerance, maxiter=max_iterations)
            return end_param
        except ValueError as e:
            raise ValueError("Parameter corresponding to the target chord length not found.") from e


class NurbsCurvePositions:
    """NurbsCurvePositions class."""

    def __init__(self, curve: NurbsCurve):
        """Initialize the NurbsCurvePositions class.

        Args:
            curve (NurbsCurve): The NurbsCurve object.
        """
        self.curve = curve

    def get_positions_length(self, num_divisions: int = 10) -> tuple[list[om.MPoint], list[float]]:
        """Get the positions length.

        Args:
            num_divisions (int): The number of divisions. Default is 10.

        Returns:
            tuple[list[om.MPoint], list[float]]: The positions and parameters.
        """
        space = om.MSpace.kWorld
        length = self.curve.fn.length()

        num_points = num_divisions
        if self.curve.form == "open":
            num_points += 1

        positions = []
        params = []
        for i in range(num_points):
            param_length = length * i / num_divisions
            param = self.curve.fn.findParamFromLength(param_length)

            positions.append(self.curve.fn.getPointAtParam(param, space=space))
            params.append(param)

        return positions, params

    def get_positions_param(self, num_divisions: int = 10) -> tuple[list[om.MPoint], list[float]]:
        """Get the positions parameter.

        Args:
            num_divisions (int): The number of divisions. Default is 10.

        Returns:
            tuple[list[om.MPoint], list[float]]: The positions and parameters.
        """
        space = om.MSpace.kWorld

        min_param, max_param = self.curve.fn.knotDomain
        param_range = max_param - min_param

        num_points = num_divisions
        if self.curve.form == "open":
            num_points += 1

        positions = []
        params = []
        for i in range(num_points):
            param = min_param + param_range * i / num_divisions
            position = self.curve.fn.getPointAtParam(param, space=space)
            positions.append(position)
            params.append(param)

        return positions, params

    def get_positions_cloud(self, num_divisions: int = 10, **kwargs) -> tuple[list[om.MPoint], list[float]]:
        """Get the positions cloud.

        Args:
            num_divisions (int): The number of divisions. Default is 10.

        Keyword Args:
            max_iterations (int): Maximum number of iterations. Default is 500.
            tolerance (float): Tolerance. Default is 1e-5.
            add_length (float): The length to add. Default is 0.1.

        Returns:
            tuple[list[om.MPoint], list[float]]: The positions and parameters.
        """
        if self.curve.form != "open":
            raise ValueError("Unsupported operation. The curve must be open.")

        max_iterations = kwargs.get("max_iterations", 500)
        tolerance = kwargs.get("tolerance", 1e-5)
        step_size = kwargs.get("add_length", 0.1)

        min_param, max_param = self.curve.fn.knotDomain

        end_point = self.curve.fn.getPointAtParam(max_param, space=om.MSpace.kWorld)

        dist_to = end_point.distanceTo

        length = 0.01
        count = 0

        while count < max_iterations:
            state = False

            params = []
            tmp_param = min_param
            for _ in range(num_divisions - 1):
                try:
                    param = self.curve.find_cloud_length_from_param(tmp_param, length, local=om.MSpace.kWorld)
                except ValueError as e:
                    raise ValueError("Parameter corresponding to the target chord length not found.") from e
                if param is not None:
                    params.append(param)
                    tmp_param = param
                else:
                    length -= step_size
                    step_size *= 0.1
                    state = True
                    break

            if state:
                continue

            end_length = dist_to(self.curve.fn.getPointAtParam(params[-1], space=om.MSpace.kWorld))
            if abs(end_length - length) < tolerance:
                break

            if end_length > length:
                length += step_size
            else:
                length -= step_size
                step_size *= 0.1

            count += 1

        logger.debug(f"Loop count: {count} of {max_iterations}")

        if count == max_iterations:
            cmds.warning("Max iterations reached.")

        params.insert(0, min_param)
        params.append(max_param)

        positions = [self.curve.fn.getPointAtParam(param, space=om.MSpace.kWorld) for param in params]

        return positions, params


class ConvertNurbsCurve:
    def __init__(self, curve: str):
        """Initialize the ModifyNurbsCurve class.

        Args:
            curve (str): The curve name.
        """
        self.curve = curve
        self.nurbs_curve = NurbsCurve(curve)

    def close_curve(self):
        """Close the curve."""
        cmds.closeCurve(self.curve, ch=False, ps=0, rpo=True)

    def insert_cvs(self, divisions: int = 1):
        """Insert CVs.

        Args:
            divisions (int): The number of divisions. Default is 1.
        """
        if divisions < 1:
            raise ValueError("Divisions must be 1 or more.")

        positions = self.nurbs_curve.get_cv_positions()
        degree = self.nurbs_curve.degree
        form_open = self.nurbs_curve.form == "open"
        num_cvs = self.nurbs_curve.num_cvs

        new_positions = []

        # Special case for 2 CVs
        if self.nurbs_curve.num_cvs == 2:
            for j in range(divisions):
                new_positions.append(positions[0] + (positions[1] - positions[0]) * (j + 1) / (divisions + 1))
            new_positions.append(positions[1])

        def _calculate_new_positions(
            nurbs_curve: NurbsCurve, target_positions: list[om.MPoint], target_lengths: list[float], open_form: bool = False
        ) -> list[om.MPoint]:
            """Calculate new positions."""
            total_length = nurbs_curve.get_length()

            result_positions = []
            for i in range(open_form and num_cvs - 1 or num_cvs):
                result_positions.append(target_positions[i])

                if target_lengths[(i + 1) % num_cvs] > target_lengths[i]:
                    length_diff = target_lengths[(i + 1) % num_cvs] - target_lengths[i]
                else:
                    length_diff = total_length - target_lengths[i] + target_lengths[(i + 1) % num_cvs]

                for j in range(divisions):
                    target_length = target_lengths[i] + length_diff * (j + 1) / (divisions + 1)
                    if target_length > total_length:
                        target_length -= total_length
                    target_param = nurbs_curve.fn.findParamFromLength(target_length)
                    target_position = nurbs_curve.fn.getPointAtParam(target_param, space=om.MSpace.kWorld)

                    result_positions.append(target_position)

            if open_form:
                result_positions.append(target_positions[-1])

            return result_positions

        # Degree 1
        if degree == 1:
            fit_curve = cmds.fitBspline(self.curve, ch=0, tol=0.01)[0]
            fit_curve_shp = cmds.listRelatives(fit_curve, s=True)[0]
            fit_nurbs_curve = NurbsCurve(fit_curve_shp)

            closest_positions, params = fit_nurbs_curve.get_closest_positions(positions)
            lengths = [fit_nurbs_curve.fn.findLengthFromParam(param) for param in params]

            new_positions = _calculate_new_positions(fit_nurbs_curve, closest_positions, lengths, form_open)

            cmds.delete(fit_curve)

        # Degree 3
        elif degree == 3:
            closest_positions, params = self.nurbs_curve.get_closest_positions(positions)
            lengths = [self.nurbs_curve.fn.findLengthFromParam(param) for param in params]

            new_positions = _calculate_new_positions(self.nurbs_curve, closest_positions, lengths, form_open)
        else:
            cmds.error("Degree is not 1 or 3. Unsupported operation.")

        new_positions = [[position.x, position.y, position.z] for position in new_positions]
        inserted_curve = cmds.listRelatives(cmds.curve(d=degree, p=new_positions), s=True)[0]

        if not form_open:
            cmds.closeCurve(inserted_curve, ch=False, ps=0, rpo=True)

        self._transfer_shape(inserted_curve)

        if degree == 3:
            self.center_curve()

    def center_curve(self, iterations: int = 100):
        """Adjust the curve to pass through the center of the CVs.

        Args:
            iterations (int): Number of iterations. Default is 100.
        """
        if self.nurbs_curve.degree != 3:
            logger.debug("Degree is not 3. Cannot center the curve.")
            return

        cv_indices = range(self.nurbs_curve.num_cvs)
        source_positions = self.nurbs_curve.get_cv_positions()

        source_positions = source_positions[:]

        if self.nurbs_curve.form == "open":
            source_positions = source_positions[1:-1]
            cv_indices = cv_indices[1:-1]

        count = 0
        while count < iterations:
            for cv_index, source_position in zip(cv_indices, source_positions, strict=False):
                closest_position, _ = self.nurbs_curve.get_closest_position(source_position)
                goal_position = source_position - closest_position
                cmds.xform(f"{self.curve}.cv[{cv_index}]", t=goal_position, ws=True, r=True)

            if all([self.nurbs_curve.fn.isPointOnCurve(source_position, space=om.MSpace.kWorld) for source_position in source_positions]):
                break

            count += 1

        if count == iterations:
            cmds.warning("Failed to center the curve.")

        logger.debug(f"Loop count: {count} of {iterations}")

    def to_fit_BSpline(self):
        """Convert to BSpline."""
        fit_curve = cmds.fitBspline(self.curve, ch=0, tol=0.01)[0]
        fit_curve_shp = cmds.listRelatives(fit_curve, s=True)[0]

        self._transfer_shape(fit_curve_shp)

    def set_degree(self, degree: int):
        """Set the degree.

        Args:
            degree (int): The degree.
        """
        if degree not in (1, 3):
            raise ValueError("Degree must be 1 or 3.")

        if degree == self.nurbs_curve.degree:
            logger.debug(f"Degree is already {degree}.")
            return

        if degree == 3 and self.nurbs_curve.num_cvs < 4:
            cmds.error("Degree is 3. The number of CVs must be 4 or more.")

        cmds.rebuildCurve(
            self.curve,
            constructionHistory=False,
            replaceOriginal=True,
            end=1,
            keepRange=0,
            keepControlPoints=True,
            keepEndPoints=False,
            keepTangents=False,
            degree=1,
        )

    def _transfer_shape(self, source_curve: str):
        """Transfer the shape, after delete the source curve.

        Args:
            source_curve (str): The source curve shape.
        """
        if cmds.nodeType(source_curve) != "nurbsCurve":
            raise ValueError("Invalid type.")

        source_nurbs_curve = NurbsCurve(source_curve)
        source_positions = source_nurbs_curve.get_cv_positions()

        curve_transform = cmds.listRelatives(self.curve, p=True)[0]
        curve_matrix = cmds.xform(curve_transform, q=True, ws=True, m=True)

        if not om.MMatrix(curve_matrix).isEquivalent(om.MMatrix.kIdentity, 1e-5):
            source_curve_transform = cmds.listRelatives(source_curve, p=True)[0]
            cmds.xform(source_curve_transform, ws=True, m=curve_matrix)
            for i, position in enumerate(source_positions):
                cmds.xform(f"{source_curve}.cv[{i}]", t=[position.x, position.y, position.z], ws=True)

        input_curve_plug = f"{self.curve}.create"
        original_curve = cmds.geometryAttrInfo(f"{self.curve}.create", originalGeometry=True)
        if original_curve:
            input_curve_plug = original_curve[0].split(".")[0] + ".create"

        cmds.connectAttr(f"{source_curve}.local", input_curve_plug, f=True)
        cmds.refresh()
        source_curve_transform = cmds.listRelatives(source_curve, p=True)[0]
        cmds.delete(source_curve_transform)
