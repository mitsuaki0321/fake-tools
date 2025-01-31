# Retarget Mesh

This tool applies the deformation of one geometry to another geometry.

![image001](images/retarget_mesh/image001.gif) 

## Overview

It applies the deformation differences between the source mesh and the destination mesh to the target mesh. Multiple destination meshes and target meshes can be selected.

## How to Use

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.retarget_mesh_ui
faketools.retarget_mesh_ui.show_ui()
```

![image001](images/retarget_mesh/image002.png) 

### Basic Usage

To use the tool, follow these steps:

1. Select the original geometry to be used for deformation and press the `Set Source Mesh` button.
2. Select the geometry to be used for deformation and press the `Set Destination Mesh` button (multiple selections possible).
3. Select the geometry to be deformed and press the `Set Target Mesh` button.
4. Press the `Retarget Mesh` button.

### Options

- **Create New Mesh**
  - If the checkbox is on, a new geometry will be created. If off, the target mesh will be deformed.

## Notes

- The topology of the source mesh and the destination mesh must be the same.
- If `Create New Mesh` is off and there are multiple destination meshes, they will not be created.
- Processing may take time if the target mesh has a large number of vertices.
