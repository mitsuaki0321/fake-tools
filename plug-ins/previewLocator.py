"""
Custom Locator Node for tool preview.

Overview:
This plugin provides a custom locator for tool previewing.
There are two types of custom locators: locator and joint.

Attributes:
    shapeType st (int): The shape type. 0: locator, 1: joint
    shapeGlobalSize sgs (float): The global size of the shape

    lineWidth lw (float): The line width
    manipulationColor mc (bool): The manipulation color flag

    shape sh (compound): The shape
        shapeColor shc (float3): The shape color
        shapeHierarchy shh (bool): The shape hierarchy flag
        shapeTransform shtr (compound): The shape transform
            shapeSize shs (float): The shape size
            shapePosition shp (float3): The shape position
            shapeRotation shr (float3): The shape rotation
"""

import sys

from maya.api import OpenMaya, OpenMayaRender, OpenMayaUI


def maya_useNewAPI():
    pass


# Plug-in locator information
k_plugin_node_name = "previewLocator"
k_plugin_node_id = OpenMaya.MTypeId(0x0007F7F7)
k_plugin_classfication = "drawdb/geometry/previewLocator"
k_draw_registrant_id = "previewLocatorNode"

# Basic settings default values
default_shape_type = 0  # 0: locator, 1: joint
default_shape_global_size = 1.0

# Drawing settings default values
default_line_width = 2.0
default_manipulation_color = False

# Shape settings default values
default_shape_color = (1.0, 1.0, 1.0)
default_shape_hierarchy = False
default_shape_size = 1.0
default_shape_position = (0.0, 0.0, 0.0)
default_shape_rotation = (0.0, 0.0, 0.0)


class PreviewLocator(OpenMayaUI.MPxLocatorNode):
    """Simple locator node.
    """

    # Attributes

    # Basic attributes
    shape_type = None
    shape_global_size = None

    # Drawing attributes
    line_width = None
    manipulation_color = None

    # Shape attributes
    shape_color = None
    shape_hierarchy = None

    shape_transform = None
    shape_size = None
    shape_position = None
    shape_rotation = None

    def __init__(self):
        """Constructor.
        """
        OpenMayaUI.MPxLocatorNode.__init__(self)

    def postConstructor(self):
        """Post constructor.
        """
        # Set the node name
        node_fn = OpenMaya.MFnDependencyNode(self.thisMObject())
        node_fn.setName("previewLocatorShape#")

    @staticmethod
    def creator():
        """Creator.
        """
        return PreviewLocator()

    @staticmethod
    def initialize():
        """Initialize the node.
        """
        enum_attr = OpenMaya.MFnEnumAttribute()
        numeric_attr = OpenMaya.MFnNumericAttribute()
        unit_attr = OpenMaya.MFnUnitAttribute()
        comp_attr = OpenMaya.MFnCompoundAttribute()
        mult_attr = OpenMaya.MFnCompoundAttribute()

        # Basic attribute

        # Shape type attribute
        PreviewLocator.shape_type = enum_attr.create("shapeType", "st", 0)
        enum_attr.addField("locator", 0)
        enum_attr.addField("joint", 1)
        enum_attr.default = default_shape_type
        enum_attr.keyable = True
        enum_attr.storable = True
        enum_attr.writable = True
        PreviewLocator.addAttribute(PreviewLocator.shape_type)

        # Size global size attribute
        PreviewLocator.shape_global_size = numeric_attr.create("shapeGlobalSize", "sgs", OpenMaya.MFnNumericData.kFloat, default_shape_global_size)
        numeric_attr.setMin(0.0)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        PreviewLocator.addAttribute(PreviewLocator.shape_global_size)

        # Drawing attribute

        # Line width attribute
        PreviewLocator.line_width = numeric_attr.create("lineWidth", "lw", OpenMaya.MFnNumericData.kFloat, default_line_width)
        numeric_attr.setMin(0.0)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        PreviewLocator.addAttribute(PreviewLocator.line_width)

        # Manipulation color attribute
        PreviewLocator.manipulation_color = numeric_attr.create("manipulationColor", "mc",
                                                                OpenMaya.MFnNumericData.kBoolean, default_manipulation_color)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        PreviewLocator.addAttribute(PreviewLocator.manipulation_color)

        # Shape attribute

        # Shape attributes
        PreviewLocator.shape = comp_attr.create("shape", "sh")
        comp_attr.array = True

        # Shape Color attribute
        PreviewLocator.shape_color = numeric_attr.createColor("shapeColor", "shc")
        numeric_attr.default = default_shape_color
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        comp_attr.addChild(PreviewLocator.shape_color)

        # Shape hierarchy attribute
        PreviewLocator.shape_hierarchy = numeric_attr.create("shapeHierarchy", "shh", OpenMaya.MFnNumericData.kBoolean, default_shape_hierarchy)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        comp_attr.addChild(PreviewLocator.shape_hierarchy)

        # Shape transform attribute
        PreviewLocator.shape_transform = mult_attr.create("shapeTransform", "shtr")
        mult_attr.array = True

        # Shape Size attribute
        PreviewLocator.shape_size = numeric_attr.create("shapeSize", "shs", OpenMaya.MFnNumericData.kFloat, default_shape_size)
        numeric_attr.setMin(0.0)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        mult_attr.addChild(PreviewLocator.shape_size)

        # Shape Position attribute
        PreviewLocator.shape_position_x = unit_attr.create("shapePositionX", "shpx", OpenMaya.MFnUnitAttribute.kDistance, 0.0)
        PreviewLocator.shape_position_y = unit_attr.create("shapePositionY", "shpy", OpenMaya.MFnUnitAttribute.kDistance, 0.0)
        PreviewLocator.shape_position_z = unit_attr.create("shapePositionZ", "shpz", OpenMaya.MFnUnitAttribute.kDistance, 0.0)
        PreviewLocator.shape_position = numeric_attr.create("shapePosition", "shp",
                                                            PreviewLocator.shape_position_x,
                                                            PreviewLocator.shape_position_y,
                                                            PreviewLocator.shape_position_z)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        mult_attr.addChild(PreviewLocator.shape_position)

        # Rotation attribute
        PreviewLocator.shape_rotation_x = unit_attr.create("shapeRotationX", "shrx", OpenMaya.MFnUnitAttribute.kAngle, 0.0)
        PreviewLocator.shape_rotation_y = unit_attr.create("shapeRotationY", "shry", OpenMaya.MFnUnitAttribute.kAngle, 0.0)
        PreviewLocator.shape_rotation_z = unit_attr.create("shapeRotationZ", "shrz", OpenMaya.MFnUnitAttribute.kAngle, 0.0)
        PreviewLocator.shape_rotation = numeric_attr.create("shapeRotation", "shr",
                                                            PreviewLocator.shape_rotation_x,
                                                            PreviewLocator.shape_rotation_y,
                                                            PreviewLocator.shape_rotation_z)
        numeric_attr.keyable = True
        numeric_attr.storable = True
        numeric_attr.writable = True
        mult_attr.addChild(PreviewLocator.shape_rotation)

        comp_attr.addChild(PreviewLocator.shape_transform)

        PreviewLocator.addAttribute(PreviewLocator.shape)

    def draw(self, view, path, style, status):
        """Draw the locator.
        """
        return None


class PreviewLocatorData(OpenMaya.MUserData):
    """Simple locator data.
    """

    def __init__(self):
        """Constructor.
        """
        OpenMaya.MUserData.__init__(self, False)  # Don't delete after draw


class PreviewLocatorDrawOverride(OpenMayaRender.MPxDrawOverride):
    """Simple locator draw override.
    """
    # Jack parameter
    line_x = [OpenMaya.MPoint(-1.0, 0.0, 0.0), OpenMaya.MPoint(1.0, 0.0, 0.0)]
    line_y = [OpenMaya.MPoint(0.0, -1.0, 0.0), OpenMaya.MPoint(0.0, 1.0, 0.0)]
    line_z = [OpenMaya.MPoint(0.0, 0.0, -1.0), OpenMaya.MPoint(0.0, 0.0, 1.0)]

    # Manipulation parameter
    manipulation_color = [OpenMaya.MColor([1.0, 0.0, 0.0]), OpenMaya.MColor([0.0, 1.0, 0.0]), OpenMaya.MColor([0.0, 0.0, 1.0])]
    line_xa = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(1.0, 0.0, 0.0)]
    line_ya = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(0.0, 1.0, 0.0)]
    line_za = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(0.0, 0.0, 1.0)]
    line_xb = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(-1.0, 0.0, 0.0)]
    line_yb = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(0.0, -1.0, 0.0)]
    line_zb = [OpenMaya.MPoint(0.0, 0.0, 0.0), OpenMaya.MPoint(0.0, 0.0, -1.0)]

    # Sphere parameter
    circle_direction = [OpenMaya.MVector(1.0, 0.0, 0.0), OpenMaya.MVector(0.0, 1.0, 0.0), OpenMaya.MVector(0.0, 0.0, 1.0)]

    def __init__(self, obj):
        """Constructor.
        """
        OpenMayaRender.MPxDrawOverride.__init__(self, obj, PreviewLocatorDrawOverride.draw)

    @staticmethod
    def creator(obj):
        """Creator.
        """
        return PreviewLocatorDrawOverride(obj)

    @staticmethod
    def draw(context, data):
        """Draw the object.
        """
        return None

    def supportedDrawAPIs(self):
        """Get the supported draw APIs.
        """
        return OpenMayaRender.MRenderer.kOpenGL | OpenMayaRender.MRenderer.kOpenGLCoreProfile | OpenMayaRender.MRenderer.kDirectX11

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        """Prepare for drawing.
        """
        data = old_data
        if not isinstance(data, PreviewLocatorData):
            data = PreviewLocatorData()

        # Basic attribute
        data.shape_type = OpenMaya.MPlug(obj_path.node(), PreviewLocator.shape_type).asInt()
        data.shape_global_size = OpenMaya.MPlug(obj_path.node(), PreviewLocator.shape_global_size).asFloat()

        # Drawing attribute
        data.line_width = OpenMaya.MPlug(obj_path.node(), PreviewLocator.line_width).asFloat()
        data.manipulation_color = OpenMaya.MPlug(obj_path.node(), PreviewLocator.manipulation_color).asBool()

        # Shape attribute
        shape_plug = OpenMaya.MPlug(obj_path.node(), PreviewLocator.shape)
        data.shape_drawable = True

        if shape_plug.isNull:
            data.shape_drawable = False
            return data

        data.shape_number = shape_plug.evaluateNumElements()
        data.shape_colors = []
        data.shape_hierarchy = []
        data.shape_sizes = []
        data.shape_positions = []
        data.shape_rotations = []

        for i in range(data.shape_number):
            shape_element = shape_plug.elementByPhysicalIndex(i)

            # Shape color
            shape_color = shape_element.child(PreviewLocator.shape_color)
            data.shape_colors.append(OpenMaya.MColor(shape_color.asMDataHandle().asFloat3()))

            # Shape hierarchy
            shape_hierarchy = shape_element.child(PreviewLocator.shape_hierarchy)
            data.shape_hierarchy.append(shape_hierarchy.asBool())

            # Shape transform
            shape_transform = shape_element.child(PreviewLocator.shape_transform)
            shape_transform_number = shape_transform.evaluateNumElements()

            shape_sizes = []
            shape_positions = []
            shape_rotations = []

            for j in range(shape_transform_number):
                shape_transform_element = shape_transform.elementByPhysicalIndex(j)

                # Size
                shape_size = shape_transform_element.child(PreviewLocator.shape_size)
                shape_sizes.append(shape_size.asFloat())

                # Position
                shape_position = shape_transform_element.child(PreviewLocator.shape_position)
                shape_positions.append(OpenMaya.MPoint(shape_position.asMDataHandle().asDouble3()))

                # Rotation
                shape_rotation = shape_transform_element.child(PreviewLocator.shape_rotation)
                shape_rotations.append(OpenMaya.MEulerRotation(shape_rotation.asMDataHandle().asDouble3()))

            data.shape_sizes.append(shape_sizes)
            data.shape_positions.append(shape_positions)
            data.shape_rotations.append(shape_rotations)

        return data

    def hasUIDrawables(self):
        """Check if the draw override has UI drawables.
        """
        return True

    def addUIDrawables(self, obj_path, draw_manager, frame_context, data):
        """Add UI drawables.
        """
        if not isinstance(data, PreviewLocatorData):
            return

        if not data.shape_drawable:
            return

        shape_type = data.shape_type
        shape_global_size = data.shape_global_size

        # If the shape type is a joint, the size is halved
        if shape_type == 1:
            shape_global_size *= 0.5

        draw_manager.beginDrawable()

        draw_manager.setLineWidth(data.line_width)
        draw_manager.setLineStyle(draw_manager.kSolid)

        transform_matrix = OpenMaya.MTransformationMatrix()
        for i in range(data.shape_number):
            color = data.shape_colors[i]
            hierarchy = data.shape_hierarchy[i]

            draw_manager.setColor(color)

            for j in range(len(data.shape_sizes[i])):
                size = data.shape_sizes[i][j] * shape_global_size
                position = data.shape_positions[i][j]
                rotation = data.shape_rotations[i][j]

                transform_matrix.setTranslation(OpenMaya.MVector(position), OpenMaya.MSpace.kWorld)
                transform_matrix.setRotation(rotation)
                transform_matrix.setScale([size, size, size], OpenMaya.MSpace.kWorld)
                m_matrix = transform_matrix.asMatrix()

                # Draw the shape
                if shape_type == 0:
                    # locator
                    if data.manipulation_color:
                        self._draw_manipulation(draw_manager, m_matrix, color)
                    else:
                        self._draw_jack(draw_manager, m_matrix)

                    if hierarchy and j > 0:
                        prev_position = data.shape_positions[i][j - 1]
                        prev_size = data.shape_sizes[i][j - 1] * shape_global_size
                        self._draw_line(draw_manager, position, prev_position)

                elif shape_type == 1:
                    # joint
                    if data.manipulation_color:
                        self._draw_manipulation(draw_manager, m_matrix, color)
                    else:
                        self._draw_jack(draw_manager, m_matrix)

                    self._draw_sphere(draw_manager, position, rotation, size)

                    if hierarchy and j > 0:
                        prev_position = data.shape_positions[i][j - 1]
                        prev_size = data.shape_sizes[i][j - 1] * shape_global_size
                        self._draw_cone(draw_manager, position, prev_position, size, prev_size)

        draw_manager.endDrawable()

    def _draw_jack(self, draw_manager, m_matrix):
        """Draw a jack.

        Args:
            draw_manager (OpenMayaRender.MUIDrawManager): The draw manager.
            m_matrix (OpenMaya.MMatrix): The matrix.
        """
        draw_manager.line(self.line_x[0] * m_matrix, self.line_x[1] * m_matrix)
        draw_manager.line(self.line_y[0] * m_matrix, self.line_y[1] * m_matrix)
        draw_manager.line(self.line_z[0] * m_matrix, self.line_z[1] * m_matrix)

    def _draw_manipulation(self, draw_manager, m_matrix, base_color):
        """Draw a manipulation.

        Args:
            draw_manager (OpenMayaRender.MUIDrawManager): The draw manager.
            m_matrix (OpenMaya.MMatrix): The matrix.
            base_color (OpenMaya.MColor): The base color.
        """
        # Manipulation color line
        draw_manager.setColor(self.manipulation_color[0])
        draw_manager.line(self.line_xa[0] * m_matrix, self.line_xa[1] * m_matrix)

        draw_manager.setColor(self.manipulation_color[1])
        draw_manager.line(self.line_ya[0] * m_matrix, self.line_ya[1] * m_matrix)

        draw_manager.setColor(self.manipulation_color[2])
        draw_manager.line(self.line_za[0] * m_matrix, self.line_za[1] * m_matrix)

        # Normal color line
        draw_manager.setColor(base_color)
        draw_manager.line(self.line_xb[0] * m_matrix, self.line_xb[1] * m_matrix)
        draw_manager.line(self.line_yb[0] * m_matrix, self.line_yb[1] * m_matrix)
        draw_manager.line(self.line_zb[0] * m_matrix, self.line_zb[1] * m_matrix)

    def _draw_sphere(self, draw_manager, center, rotation, scale):
        """Draw a sphere.

        Args:
            draw_manager (OpenMayaRender.MUIDrawManager): The draw manager.
            center (OpenMaya.MPoint): The center.
            rotation (OpenMaya.MEulerRotation): The rotation.
            scale (float): The scale.
        """
        draw_manager.circle(center, self.circle_direction[0].rotateBy(rotation), scale, False)
        draw_manager.circle(center, self.circle_direction[1].rotateBy(rotation), scale, False)
        draw_manager.circle(center, self.circle_direction[2].rotateBy(rotation), scale, False)

    def _draw_cone(self, draw_manager, position_a, position_b, scale_a, scale_b):
        """Draw a cone.

        Args:
            draw_manager (OpenMayaRender.MUIDrawManager): The draw manager.
            position_a (OpenMaya.MPoint): The position A is the tip point.
            position_b (OpenMaya.MPoint): The position B is the base point.
            scale_a (float): The scale A is the tip scale.
            scale_b (float): The scale B is the base scale.
        """
        vector_a_b = position_a - position_b

        direction = vector_a_b.normal()
        base_point = position_b + direction * scale_b
        height = vector_a_b.length() - scale_a - scale_b

        draw_manager.cone(base_point, direction, scale_b, height, 4, False)

    def _draw_line(self, draw_manager, point_a, point_b):
        """Draw a line.

        Args:
            draw_manager (OpenMayaRender.MUIDrawManager): The draw manager.
            point_a (OpenMaya.MPoint): The point A.
            point_b (OpenMaya.MPoint): The point B.
        """
        draw_manager.line(point_a, point_b)


def initializePlugin(plugin):
    """Initialize the plug-in.
    """
    plugin_fn = OpenMaya.MFnPlugin(plugin, "Mitsuaki Watanabe", "1.0", "Any")
    try:
        plugin_fn.registerNode(k_plugin_node_name,
                               k_plugin_node_id,
                               PreviewLocator.creator,
                               PreviewLocator.initialize,
                               OpenMaya.MPxNode.kLocatorNode,
                               k_plugin_classfication
                               )
    except Exception as e:
        sys.stderr.write(f"Failed to register node: {e}")
        raise e

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(k_plugin_classfication,
                                                                 k_draw_registrant_id,
                                                                 PreviewLocatorDrawOverride.creator
                                                                 )
    except Exception as e:
        sys.stderr.write(f"Failed to register node: {e}")
        raise e


def uninitializePlugin(plugin):
    """Uninitialize the plug-in.
    """
    plugin_fn = OpenMaya.MFnPlugin(plugin)
    try:
        plugin_fn.deregisterNode(k_plugin_node_id)
    except Exception as e:
        sys.stderr.write(f"Failed to deregister node: {e}")
        raise e

    try:
        OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(k_plugin_classfication,
                                                                   k_draw_registrant_id
                                                                   )
    except Exception as e:
        sys.stderr.write(f"Failed to deregister node: {e}")
        raise e
