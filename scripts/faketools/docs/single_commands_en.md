# Single Commands

Provides single commands.

## How to Use

Execute the command from the dedicated menu.

![image001](images/single_commands//image001.png)

### Basic Usage

Select and execute the command from the menu.

The method of selecting nodes varies depending on the command. There are three types of commands:

**Scene Command**  
Commands executed on the entire scene. They are executed regardless of selection.

**All Command**  
Commands executed on all selected nodes.

**Pair Command**  
Commands executed on nodes selected after the first selected node, based on the first selected node.

## Command List

### Scene Command

- **OptimizeScene**
  - Optimizes the scene.
    - Removes unknown plugins.
    - Deletes unknown nodes.
    - Deletes unused nodes.
    - Deletes DataStructure.

### All Command

- **LockAndHide**
  - Locks and hides attributes displayed in the channel box of the selected nodes.
  - If attributes are directly selected in the channel box, it applies only to those attributes.
  - Visibility is hidden but not locked.
  
- **UnlockAndShow**
  - Resets the display in the channel box to the state when the node was created.
  - Dynamic attributes (user-defined attributes) are not considered.
  
- **BreakConnections**
  - Breaks connections of attributes displayed in the channel box of the selected nodes.
  - If attributes are directly selected in the channel box, it applies only to those attributes.

- **FreezeTransform**
  - Freezes the transform of the selected nodes and resets the pivot.

- **FreezeVertices**
  - Freezes the vertices of the selected mesh.

- **FreezeImmediateVertices**
  - Freezes the vertices of the selected ImmediateObject mesh.

- **ParentConstraint**
  - Creates a Locator at the position of the selected nodes and ParentConstraints it to the selected nodes.

- **DeleteConstraint**
  - Deletes the Constraint of the selected nodes.

- **ChainJoints**
  - Sets the selected nodes in a chain parent-child relationship.

- **MirrorJoints**
  - Mirrors the selected nodes on the YZ plane.

- **DeleteDynamicAttributes**
  - Deletes all dynamic attributes (user-defined attributes) of the selected nodes.
  - Locked attributes are also deleted.

### Pair Command

- **SnapPosition**
  - Snaps the position of the first selected node to the position of the subsequently selected nodes.

- **SnapRotation**
  - Snaps the rotation of the first selected node to the rotation of the subsequently selected nodes.

- **SnapScale**
  - Snaps the scale of the first selected node to the scale of the subsequently selected nodes.

- **SnapTranslateAndRotate**
  - Snaps the position and rotation of the first selected node to the position and rotation of the subsequently selected nodes.

- **CopyTransform**
  - Copies the Translate, Rotate, and Scale of the first selected node to the subsequently selected nodes.

- **ConnectTransform**
  - Connects the Translate, Rotate, and Scale of the first selected node to the subsequently selected nodes.

- **CopyWeight**
  - Copies the SkinCluster weights of the first selected node to the subsequently selected nodes.
  - If the subsequently selected nodes do not have a SkinCluster, a SkinCluster is automatically created.

- **ConnectTopology**
  - Connects the topology of the first selected node to the subsequently selected nodes.
  
- **CopyTopology**
  - Copies the topology of the first selected node to the subsequently selected nodes.

- **Parent**
  - Sets the first selected node as the parent of the subsequently selected nodes.




