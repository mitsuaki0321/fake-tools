"""Component filter functions for filtering components by type."""

from logging import getLogger

import maya.api.OpenMaya as om
import maya.cmds as cmds

logger = getLogger(__name__)


class ComponentFilter:
    def __init__(self, components: list[str]):
        """Initialize the component filter with a list of components.

        Args:
            components (list[str]): List of component names
        """
        self._selection_list = om.MSelectionList()
        self.add_selection_list(components)

    def add_selection_list(self, components: list[str]) -> None:
        """Add components to the selection list."""
        for component in components:
            self._selection_list.add(component)

    def clear_selection_list(self) -> None:
        """Clear the selection list."""
        self._selection_list.clear()

    def has_component(self) -> bool:
        """Check if the selection list has any components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kComponent)
        return not it_selection_list.isDone()

    def has_vertex(self) -> bool:
        """Check if the selection list has vertex components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kMeshVertComponent)
        return not it_selection_list.isDone()

    def has_edge(self) -> bool:
        """Check if the selection list has edge components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kMeshEdgeComponent)
        return not it_selection_list.isDone()

    def has_face(self) -> bool:
        """Check if the selection list has face components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kMeshPolygonComponent)
        return not it_selection_list.isDone()

    def has_curve_cv(self) -> bool:
        """Check if the selection list has curve CV components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kCurveCVComponent)
        return not it_selection_list.isDone()

    def has_curve_ep(self) -> bool:
        """Check if the selection list has curve EP components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kCurveEPComponent)
        return not it_selection_list.isDone()

    def has_surface_cv(self) -> bool:
        """Check if the selection list has surface CV components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kSurfaceCVComponent)
        return not it_selection_list.isDone()

    def has_lattice_point(self) -> bool:
        """Check if the selection list has lattice point components."""
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kLatticeComponent)
        return not it_selection_list.isDone()

    def get_vertex_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of vertex components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[int]]: The mesh shape name and vertex indices.
        """
        component_data = self.__get_single_components(om.MFn.kMeshVertComponent)
        if as_component_name and component_data:
            for shape, indices in component_data.items():
                geometry = cmds.listRelatives(shape, parent=True, path=True)[0]
                component_data[shape] = [f"{geometry}.vtx[{i}]" for i in indices]

        return component_data

    def get_edge_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of edge components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[int]]: The mesh shape name and edge indices.
        """
        component_data = self.__get_single_components(om.MFn.kMeshEdgeComponent)
        if as_component_name and component_data:
            for shape, indices in component_data.items():
                geometry = cmds.listRelatives(shape, parent=True, path=True)[0]
                component_data[shape] = [f"{geometry}.e[{i}]" for i in indices]

        return component_data

    def get_face_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of face components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[int]]: The mesh shape name and face indices.
        """
        component_data = self.__get_single_components(om.MFn.kMeshPolygonComponent)
        if as_component_name and component_data:
            for shape, indices in component_data.items():
                geometry = cmds.listRelatives(shape, parent=True, path=True)[0]
                component_data[shape] = [f"{geometry}.f[{i}]" for i in indices]

        return component_data

    def get_curve_cv_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of curve CV components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[int]]: The nurbsCurve shape name and CV indices.
        """
        component_data = self.__get_single_components(om.MFn.kCurveCVComponent)
        if as_component_name and component_data:
            for shape, indices in component_data.items():
                component_data[shape] = [f"{shape}.cv[{i}]" for i in indices]

        return component_data

    def get_curve_ep_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of curve EP components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[int]]: The nurbsCurve shape name and EP indices.
        """
        component_data = self.__get_single_components(om.MFn.kCurveEPComponent)
        if as_component_name and component_data:
            for shape, indices in component_data.items():
                component_data[shape] = [f"{shape}.ep[{i}]" for i in indices]

        return component_data

    def get_surface_cv_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of surface CV components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[tuple[int, int]]]: The nurbsSurface shape name and UV indices ( pair indices ).
        """
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kSurfaceCVComponent)
        if it_selection_list.isDone():
            return {}

        result_components = {}
        while not it_selection_list.isDone():
            node, component = it_selection_list.getComponent()
            double_index_component = om.MFnDoubleIndexedComponent(component)
            result_components[node.partialPathName()] = double_index_component.getElements()
            it_selection_list.next()

        logger.debug(f"Found components: {result_components}")

        if as_component_name and result_components:
            for shape, indices in result_components.items():
                geometry = cmds.listRelatives(shape, parent=True, path=True)[0]
                result_components[shape] = [f"{geometry}.cv[{i[0]}][{i[1]}]" for i in indices]

        return result_components

    def get_lattice_point_components(self, as_component_name: bool = False) -> dict[str, list[int]]:
        """Get a list of lattice point components.

        Args:
            as_component_name (bool): Return the component name instead of the index.

        Returns:
            dict[str, list[tuple[int, int, int]]]: The lattice shape name and lattice indices ( tuple indices ).
        """
        it_selection_list = om.MItSelectionList(self._selection_list, om.MFn.kLatticeComponent)
        if it_selection_list.isDone():
            return {}

        result_components = {}
        while not it_selection_list.isDone():
            node, component = it_selection_list.getComponent()
            triple_index_component = om.MFnTripleIndexedComponent(component)
            result_components[node.partialPathName()] = triple_index_component.getElements()
            it_selection_list.next()

        logger.debug(f"Found components: {result_components}")

        if as_component_name and result_components:
            for shape, indices in result_components.items():
                geometry = cmds.listRelatives(shape, parent=True, path=True)[0]
                result_components[shape] = [f"{geometry}.pt[{i[0]}][{i[1]}][{i[2]}]" for i in indices]

        return result_components

    def get_components(self, component_type: list[str]) -> dict[str, list[int]]:
        """Get a list of components by type.

        Args:
            component_type (list[str]): List of component types.

        Returns:
            dict[str, list[int]]: The shape name and component indices.
        """
        component_data = {}
        for component in component_type:
            if component == "vertex":
                component_data.update(self.get_vertex_components(as_component_name=True))
            elif component == "edge":
                component_data.update(self.get_edge_components(as_component_name=True))
            elif component == "face":
                component_data.update(self.get_face_components(as_component_name=True))
            elif component == "curve_cv":
                component_data.update(self.get_curve_cv_components(as_component_name=True))
            elif component == "curve_ep":
                component_data.update(self.get_curve_ep_components(as_component_name=True))
            elif component == "surface_cv":
                component_data.update(self.get_surface_cv_components(as_component_name=True))
            elif component == "lattice_point":
                component_data.update(self.get_lattice_point_components(as_component_name=True))
            else:
                logger.warning(f"Unknown component type: {component}")

        return component_data

    def __get_single_components(self, component_type: om.MFn.kComponent) -> dict[str, list[int]]:
        """Get a list of single components.

        Args:
            component_type (om.MFn.kComponent): The component type.

        Returns:
            dict[str, list[int]]: The shape name and component indices.
        """
        it_selection_list = om.MItSelectionList(self._selection_list, component_type)
        if it_selection_list.isDone():
            return {}

        result_components = {}
        while not it_selection_list.isDone():
            node, component = it_selection_list.getComponent()
            single_index_component = om.MFnSingleIndexedComponent(component)
            result_components[node.partialPathName()] = list(single_index_component.getElements())
            it_selection_list.next()

        logger.debug(f"Found components: {result_components}")

        return result_components


class ComponentSelection:
    def __init__(self, components: list[str]):
        """Initialize the component selection with a list of components.

        Notes:
            - Only mesh, nurbsCurve, nurbsSurface, and lattice components are supported.

        Args:
            components (list[str]): List of component names
        """
        if not components:
            raise ValueError("Components are not specified.")

        components = cmds.filterExpand(components, sm=[28, 31, 32, 34, 46], ex=True)
        if not components:
            raise ValueError("Components are not supported. Only mesh, nurbsCurve, nurbsSurface, and lattice components are supported.")

        self._components = components

    def _get_positions(self) -> list[float]:
        """Get the component positions.

        Returns:
            list[float]: The component positions.
        """
        positions = cmds.xform(self._components, q=True, ws=True, t=True)
        return list(zip(positions[::3], positions[1::3], positions[2::3], strict=False))

    def reverse_selection(self) -> list[str]:
        """Reverse selection of components.

        Notes:
            - When executed, the selected components will be inverted.

        Returns:
            list[str]: The reversed selected components.
        """
        cmds.select(self._components, r=True)
        cmds.InvertSelection()
        return cmds.ls(sl=True, fl=True)

    def unique_selection(self) -> list[str]:
        """Unique selection of components.

        Notes:
            - Need to soft select or symmetry enabled, before calling this function.

        Returns:
            list[str]: The unique selected components.
        """
        cmds.select(self._components, r=True)
        return list(get_unique_selections().keys())

    def x_area_selection(self, area: str = "center") -> list[str]:
        """X area selection of components.

        Args:
            area (str): The area to select components. Default is 'center'. Options are 'center', 'left', and 'right'.

        Returns:
            list[str]: The area selected components.
        """
        if area not in ["center", "left", "right"]:
            raise ValueError(f"Invalid area: {area}")

        positions = self._get_positions()

        if area == "center":
            result_components = [component for component, position in zip(self._components, positions, strict=False) if 0.001 > position[0] > -0.001]
            logger.debug(f"Center area components: {result_components}")
        elif area == "left":
            result_components = [component for component, position in zip(self._components, positions, strict=False) if position[0] > 0.001]
            logger.debug(f"Left area components: {result_components}")
        elif area == "right":
            result_components = [component for component, position in zip(self._components, positions, strict=False) if position[0] < -0.001]
            logger.debug(f"Right area components: {result_components}")

        logger.debug(f"X area components: {result_components}")

        return result_components

    def same_position_selection(self, driver_mesh: str, **kwargs) -> list[str]:
        """Same position selection of components.

        Notes:
            - Driver object only supports mesh geometry.

        Args:
            driver_mesh (str): The driver mesh object.

        Returns:
            list[str]: The same position selected components.
        """
        max_distance = kwargs.get("max_distance", 0.001)

        if not driver_mesh:
            raise ValueError("Driver mesh is not specified.")

        if not cmds.objExists(driver_mesh):
            raise ValueError(f"Driver mesh does not exist: {driver_mesh}")

        if cmds.nodeType(driver_mesh) != "mesh":
            raise ValueError(f"Driver mesh is not a mesh: {driver_mesh}")

        selection_list = om.MSelectionList()
        selection_list.add(driver_mesh)
        mesh_dag_path = selection_list.getDagPath(0)

        mesh_intersector = om.MMeshIntersector()
        mesh_intersector.create(mesh_dag_path.node(), mesh_dag_path.inclusiveMatrix())

        component_positions = self._get_positions()

        result_components = []
        for component, position in zip(self._components, component_positions, strict=False):
            component_point = om.MPoint(position)
            point_on_mesh = mesh_intersector.getClosestPoint(component_point, max_distance)

            if point_on_mesh is not None:
                continue

            result_components.append(component)

        logger.debug(f"Same position components: {result_components}")

        return result_components

    def uv_area_selection(self, **kwargs) -> list[str]:
        """UV area selection of components.

        Notes:
            - Only nurbsCurve and nurbsSurface components are supported.

        Returns:
            list[str]: The parameter selected components.
        """
        uv = kwargs.get("uv", "u")
        area = kwargs.get("area", [0.0, 1.0])  # min, max

        components = cmds.filterExpand(self._components, sm=28, ex=True)
        if not components:
            raise ValueError("Components are not supported. Only nurbsCurve and nurbsSurface components are supported.")

        if uv not in ["u", "v"]:
            raise ValueError(f"Invalid parameter. u or v: {uv}")

        if len(area) != 2:
            raise ValueError("Invalid parameter area. Must be a list of two values.")

        if area[0] > area[1]:
            raise ValueError("Invalid parameter area. Minimum value is greater than maximum value.")

        result_components = []

        filter_components = ComponentFilter(components)
        if filter_components.has_curve_cv():
            component_data = filter_components.get_curve_cv_components()
            for shape, indices in component_data.items():
                shape_transform = cmds.listRelatives(shape, parent=True, path=True)[0]
                for index in indices:
                    if area[0] <= index <= area[1]:
                        result_components.append(f"{shape_transform}.cv[{index}]")

        if filter_components.has_surface_cv():
            component_data = filter_components.get_surface_cv_components()
            for shape, indices in component_data.items():
                shape_transform = cmds.listRelatives(shape, parent=True, path=True)[0]
                for index in indices:
                    if uv == "u":
                        if area[0] <= index[0] <= area[1]:
                            result_components.append(f"{shape_transform}.cv[{index[0]}][{index[1]}]")
                    elif uv == "v" and area[0] <= index[1] <= area[1]:
                        result_components.append(f"{shape_transform}.cv[{index[0]}][{index[1]}]")

        logger.debug(f"Parameter components: {result_components}")

        return result_components


def get_unique_selections(filter_geometries: list[str] | None = None) -> dict[str, float]:
    """Get the unique components.

    Args:
        filter_geometries (list[str]): List of geometry names to filter the components.

    Returns:
        dict[str, float]: The selected components with their weights.
    """
    if filter_geometries is None:
        filter_geometries_path = []
    else:
        filter_geometries_path = []
        for geometry in filter_geometries:
            if not cmds.objExists(geometry):
                raise ValueError(f"Geometry does not exist: {geometry}")

            if cmds.nodeType(geometry) != "mesh":
                raise ValueError(f"Geometry is not a mesh: {geometry}")

            selection_list = om.MSelectionList()
            selection_list.add(geometry)
            dag_path = selection_list.getDagPath(0)

            filter_geometries_path.append(dag_path)

    rich_selection = om.MGlobal.getRichSelection()
    selection = rich_selection.getSelection()
    sym_selection = rich_selection.getSymmetry()
    if selection.isEmpty():
        logger.debug("No selection found.")
        return {}

    if not sym_selection.isEmpty():
        selection.merge(sym_selection)

    elements = {}

    def _process_single_indexed(selection_list, attr_list):
        for component_type, attr in zip(selection_list, attr_list, strict=False):
            iterator = om.MItSelectionList(selection, component_type)
            while not iterator.isDone():
                dag_path, component = iterator.getComponent()
                if filter_geometries_path and dag_path not in filter_geometries_path:
                    iterator.next()
                    continue

                dag_path.pop()  # Remove shape node
                node = dag_path.partialPathName()
                fn_comp = om.MFnSingleIndexedComponent(component)
                for i in range(fn_comp.elementCount):
                    index = fn_comp.element(i)
                    weight = fn_comp.weight(i).influence if fn_comp.hasWeights else 1.0
                    elements[f"{node}.{attr}[{index}]"] = weight

                logger.debug(f"Found components: {elements}")

                iterator.next()

    def _process_double_indexed(selection_list, attr_list):
        for component_type, attr in zip(selection_list, attr_list, strict=False):
            iterator = om.MItSelectionList(selection, component_type)
            while not iterator.isDone():
                dag_path, component = iterator.getComponent()
                if filter_geometries_path and dag_path not in filter_geometries_path:
                    iterator.next()
                    continue

                dag_path.pop()
                node = dag_path.partialPathName()
                fn_comp = om.MFnDoubleIndexedComponent(component)
                for i in range(fn_comp.elementCount):
                    u, v = fn_comp.getElement(i)
                    weight = fn_comp.weight(i).influence if fn_comp.hasWeights else 1.0
                    elements[f"{node}.{attr}[{u}][{v}]"] = weight

                logger.debug(f"Found components: {elements}")

                iterator.next()

    def _process_triple_indexed(selection_list, attr_list):
        for component_type, attr in zip(selection_list, attr_list, strict=False):
            iterator = om.MItSelectionList(selection, component_type)
            while not iterator.isDone():
                dag_path, component = iterator.getComponent()
                if filter_geometries_path and dag_path not in filter_geometries_path:
                    iterator.next()
                    continue

                dag_path.pop()
                node = dag_path.partialPathName()
                fn_comp = om.MFnTripleIndexedComponent(component)
                for i in range(fn_comp.elementCount):
                    s, t, u = fn_comp.getElement(i)
                    weight = fn_comp.weight(i).influence if fn_comp.hasWeights else 1.0
                    elements[f"{node}.{attr}[{s}][{t}][{u}]"] = weight

                logger.debug(f"Found components: {elements}")

                iterator.next()

    _process_single_indexed(
        [om.MFn.kCurveCVComponent, om.MFn.kCurveEPComponent, om.MFn.kMeshVertComponent, om.MFn.kMeshEdgeComponent, om.MFn.kMeshPolygonComponent],
        ["cv", "ep", "vtx", "e", "f"],
    )

    _process_double_indexed(
        [om.MFn.kSurfaceCVComponent, om.MFn.kSubdivCVComponent, om.MFn.kSubdivEdgeComponent, om.MFn.kSubdivFaceComponent], ["cv", "smp", "sme", "smf"]
    )

    _process_triple_indexed([om.MFn.kLatticeComponent], ["pt"])

    return elements
