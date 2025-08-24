"""
Transfer the skin weights.
"""

import json
from logging import getLogger
import os
import pickle

import maya.cmds as cmds

from ..lib import lib_skinCluster

logger = getLogger(__name__)


class SkinWeightsCopyPaste:
    """SkinCluster weights copy and paste class."""

    def __init__(
        self,
        *,
        method: str = "oneToAll",
        blend_weights: float = 1.0,
    ):
        """Initialize the skin weights copy and paste.

        Args:
            method (str, optional): The method. Defaults to 'oneToAll'. 'oneToAll' or 'oneToOne'.
            blend_weights (float, optional): The blend weights. Defaults to 1.0.
        """
        if method not in ["oneToAll", "oneToOne"]:
            raise ValueError(f"Invalid method: {method}")

        self._method = method

        if not 0.0 <= blend_weights <= 1.0:
            raise ValueError(f"Invalid blend weights: {blend_weights}")

        self._blend_weights = blend_weights

        self._src_components = []
        self._src_weights = []
        self._src_skinCluster = None

        self._dst_components = []
        self._dst_weights = []
        self._dst_skinCluster = None

    @property
    def method(self) -> str:
        """Get the method.

        Returns:
            str: The method.
        """
        return self._method

    def set_method(self, method: str) -> None:
        """Set the method.

        Args:
            method (str): The method.
        """
        if self.get_num_dst_components() != 0:
            raise ValueError("Cannot change the method after setting the destination components.")

        if not isinstance(method, str):
            raise ValueError(f"Invalid method: {method}")

        if method not in ["oneToAll", "oneToOne"]:
            raise ValueError(f"Invalid method: {method}")

        self._method = method

        logger.debug(f"Set method: {method}")

    @property
    def blend_weights(self) -> float:
        """Get the blend weights.

        Returns:
            float: The blend weights.
        """
        return self._blend_weights

    def set_blend_weights(self, blend_weights: float) -> None:
        """Set the blend weights.

        Args:
            blend_weights (float): The blend weights.
        """
        if not isinstance(blend_weights, float):
            raise ValueError(f"Invalid blend weights: {blend_weights}")

        if not 0.0 <= blend_weights <= 1.0:
            raise ValueError(f"Invalid blend weights: {blend_weights}")

        self._blend_weights = blend_weights

        logger.debug(f"Set blend weights: {blend_weights}")

    def set_src_components(self, components: list[str]) -> None:
        """Set the source components.

        Args:
            components (list[str]): The source components.
        """
        if not components:
            raise ValueError("No components specified.")

        components = cmds.ls(components, flatten=True)
        filter_components = cmds.filterExpand(components, sm=[28, 31, 46], ex=True)
        if len(filter_components) != len(components):
            cmds.error("Invalid components or objects selected.")

        shapes = list(set(cmds.ls(components, objectsOnly=True)))
        if len(shapes) > 1:
            cmds.error("Multiple shapes selected.")

        skinCluster = lib_skinCluster.get_skinCluster(shapes[0])
        if not skinCluster:
            cmds.error("No skinCluster found.")

        self._src_components = components
        self._src_skinCluster = skinCluster

        # Reset destination components
        self._dst_components = []
        self._dst_weights = []
        self._dst_skinCluster = None

        logger.debug(f"Set source components: {self._src_components}")

    def get_src_components(self) -> list[str]:
        """Get the source components.

        Returns:
            list[str]: The source components.
        """
        return self._src_components

    def clear_src_components(self) -> None:
        """Clear the source components."""
        self._src_components = []
        self._src_skinCluster = None

        self.clear_dst_components()

        logger.debug("Clear source components")

    def get_num_src_components(self) -> int:
        """Get the number of source components.

        Returns:
            int: The number of source components.
        """
        return len(self._src_components)

    def set_dst_components(self, components: list[str]) -> None:
        """Set the destination components.

        Args:
            components (list[str]): The destination components.
        """
        if not components:
            raise ValueError("No components specified.")

        if not self._src_components:
            cmds.error("No source components")

        components = cmds.ls(components, flatten=True)
        filter_components = cmds.filterExpand(components, sm=[28, 31, 46])
        if len(filter_components) != len(components):
            cmds.error("Invalid components or objects selected.")

        shapes = list(set(cmds.ls(components, objectsOnly=True)))
        if len(shapes) > 1:
            cmds.error("Multiple shapes selected.")

        if self._method == "oneToOne" and len(self._src_components) != len(components):
            cmds.error(f"The source and destination components do not match: {self._src_components} != {components}")

        skinCluster = lib_skinCluster.get_skinCluster(shapes[0])
        if not skinCluster:
            cmds.error("No skinCluster found.")

        self._dst_skinCluster = skinCluster
        self._dst_components = components
        self._dst_weights = lib_skinCluster.get_skin_weights(skinCluster, components)

        src_weights = lib_skinCluster.get_skin_weights(self._src_skinCluster, self._src_components)
        src_infs = cmds.skinCluster(self._src_skinCluster, q=True, inf=True)
        dst_infs = cmds.skinCluster(self._dst_skinCluster, q=True, inf=True)

        self._src_weights = []
        for src_weight in src_weights:
            order_weight = []
            for dst_inf in dst_infs:
                if dst_inf in src_infs:
                    order_weight.append(src_weight[src_infs.index(dst_inf)])
                else:
                    order_weight.append(0.0)

            self._src_weights.append(order_weight)

        if self._method == "oneToAll":
            self._src_weights = [self._src_weights[0]] * len(self._dst_components)

        logger.debug(f"Set destination components: {self._dst_components}")

    def get_dst_components(self) -> list[str]:
        """Get the destination components.

        Returns:
            list[str]: The destination components.
        """
        return self._dst_components

    def clear_dst_components(self) -> None:
        """Clear the destination components."""
        self._src_weights = []

        self._dst_components = []
        self._dst_weights = []
        self._dst_skinCluster = None

        logger.debug("Clear destination components")

    def get_num_dst_components(self) -> int:
        """Get the number of destination components.

        Returns:
            int: The number of destination components.
        """
        return len(self._dst_components)

    def is_pastable(self) -> bool:
        """Return True if the paste is ready.

        Returns:
            bool: True if the paste is ready.
        """
        if not self._src_components:
            logger.debug("No source components")
            return False

        if not self._dst_components:
            logger.debug("No destination components")
            return False

        if not self._src_weights:
            logger.debug("No source weights")
            return False

        if not self._dst_weights:
            logger.debug("No destination weights")
            return False

        if not self._src_skinCluster:
            logger.debug("No source skinCluster")
            return False

        if not self._dst_skinCluster:
            logger.debug("No destination skinCluster")
            return False

        return True

    def paste_skinWeights(self) -> None:
        """Paste the skin weights."""
        if not self.is_pastable():
            cmds.error("Copy and paste is not ready.")

        new_weights = []
        for src_weight, dst_weight in zip(self._src_weights, self._dst_weights, strict=False):
            new_weight = []
            for src_w, dst_w in zip(src_weight, dst_weight, strict=False):
                new_weight.append(src_w * self._blend_weights + dst_w * (1.0 - self._blend_weights))

            new_weights.append(new_weight)

        lib_skinCluster.set_skin_weights(self._dst_skinCluster, new_weights, self._dst_components)

        logger.debug(f"Copy and paste skin weights: {self._src_skinCluster} -> {self._dst_skinCluster}")


class SkinWeightsImportExport:
    """SkinCluster weights export and import class."""

    def export_weights(self, skinCluster: str, path: str, format: str = "json"):
        """Export the skin weights.

        Args:
            path (str): The output directory.
            format (str, optional): The file format. Defaults to 'json'. 'json' or 'pickle'.
        """
        # Validate
        if format not in ["json", "pickle"]:
            raise ValueError(f"Invalid format: {format}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        # Get data
        influence = self._get_influences(skinCluster)
        geometry = self._get_geometry(skinCluster)
        geometry_type = cmds.nodeType(geometry)
        components = self._get_components(skinCluster)
        num_components = self._get_num_components(geometry)
        weights = lib_skinCluster.get_skin_weights_custom(skinCluster, all_components=True)

        data = {
            "influence": influence,
            "geometry": geometry,
            "geometryType": geometry_type,
            "components": components,
            "numComponents": num_components,
            "weights": weights,
        }

        # Write data
        if format == "json":
            output_path = os.path.join(path, f"{self._skinCluster}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=4)

            logger.debug(f"Export skin weights: {output_path}")
        else:
            output_path = os.path.join(path, f"{self._skinCluster}.pkl")
            with open(output_path, "wb") as f:
                pickle.dump(data, f)

            logger.debug(f"Export skin weights: {output_path}")

    def import_weights(self, file_path: str, target_geometry: str | None = None):
        """Import the skin weights.

        Args:
            file_path (str): The file path.
            target_geometry (str, optional): The target geometry. Defaults to None.
        """
        # Read data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if not file_path.endswith(".json") and not file_path.endswith(".pkl"):
            raise ValueError(f"Invalid file format: {file_path}")

        if file_path.endswith(".json"):
            with open(file_path) as f:
                data = json.load(f)
        else:
            with open(file_path, "rb") as f:
                data = pickle.load(f)

        if not data:
            raise ValueError(f"Invalid data: {file_path}")

        # Validate data
        if not all([key in data for key in ["influence", "geometry", "geometryType", "components", "numComponents", "weights"]]):
            raise ValueError(f"Invalid data: {file_path}")

        if not target_geometry:
            target_geometry = data["geometry"]

        if not cmds.objExists(target_geometry):
            cmds.error(f"Node does not exist: {target_geometry}")

        if cmds.nodeType(target_geometry) != data["geometryType"]:
            cmds.error(f"Invalid geometry type: {target_geometry}")

        if self._get_num_components(target_geometry) != data["numComponents"]:
            cmds.error(f"Invalid number of components: {target_geometry}")

        skinCluster = lib_skinCluster.get_skinCluster(target_geometry)
        infs = data["influence"]
        if not skinCluster:
            error_infs = [inf for inf in infs if not cmds.objExists(inf)]
            if error_infs:
                cmds.error(f"Influence does not exist: {error_infs}")

            target_skinCluster = cmds.skinCluster(data["influence"], target_geometry, tsb=True)[0]

            logger.debug(f"Create skinCluster: {target_geometry}")
        else:
            current_infs = cmds.skinCluster(target_skinCluster, q=True, inf=True)
            if current_infs != infs:
                cmds.error(f"Influence does not match: {skinCluster}")

        # Import weights
        lib_skinCluster.set_skin_weights_custom(target_skinCluster, data["weights"], data["components"])

        logger.debug(f"Import skin weights: {file_path}")

    @staticmethod
    def _is_skinCluster(node: str) -> bool:
        """Check if the node is a skinCluster.

        Args:
            node (str): The node.

        Returns:
            bool: True if the node is a skinCluster, False otherwise.
        """
        if not cmds.objExists(node):
            return False

        return cmds.nodeType(node) == "skinCluster"

    def _get_influences(self, skinCluster: str) -> list[str]:
        """Get the influences.

        Args:
            skinCluster (str): The skinCluster node.

        Returns:
            list[str]: The influences.
        """
        if not self._is_skinCluster(skinCluster):
            raise ValueError(f"Node is not a skinCluster: {skinCluster}")

        return cmds.skinCluster(skinCluster, q=True, inf=True)

    def _get_geometry(self, skinCluster: str) -> str:
        """Get the geometry.

        Args:
            skinCluster (str): The skinCluster node.

        Returns:
            str: The geometry.
        """
        if not self._is_skinCluster(skinCluster):
            raise ValueError(f"Node is not a skinCluster: {self._skinCluster}")

        return cmds.skinCluster(skinCluster, q=True, g=True)[0]

    def _get_components(self, skinCluster: str) -> list[str]:
        """Get the components.

        Args:
            skinCluster (str): The skinCluster node.

        Returns:
            list[str]: The components.
        """
        if self._is_skinCluster(skinCluster):
            raise ValueError(f"Node is not a skinCluster: {self._skinCluster}")

        return cmds.skinCluster(skinCluster, q=True, components=True)

    def _get_num_components(self, geometry: str) -> int:
        """Get the number of components.

        Args:
            geometry (str): The geometry.

        Returns:
            int: The number of components.
        """
        if not cmds.objExists(geometry):
            raise ValueError(f"Node does not exist: {geometry}")

        return len(cmds.ls(f"{geometry}.cp[*]", flatten=True))
