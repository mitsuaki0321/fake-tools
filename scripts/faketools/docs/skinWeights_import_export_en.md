# SkinWeights Import/Export

This tool allows you to import and export skin weights.

## How to Use

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.tools.skinWeights_import_export
faketools.tools.skinWeights_import_export.show_ui()
```

![image001](images/skinWeights_import_export/image001.png)

### Basic Usage

There are two modes: Quick Mode for temporarily saving skin weights and Advanced Mode for saving to a file.

#### Quick Mode

**Export**

1. Select the geometry.
2. Press the `Export` button to save the skin weights. The weights are saved in the temporary directory of your OS.

**Import**

1. Press the `Import` button to load the saved skin weights.

#### Advanced Mode

**Export**

1. Select the geometry.
2. Choose the file format: `json` or `pickle`.
3. Enter the group name (folder name) for export.
4. Press the `Export` button to save the skin weights.

**Import**

1. Select the group or file to import from the tree view.
2. Press the `Import` button to load the saved skin weights.

#### About Import

- If geometry is selected, the number of selected geometries must match the number of files selected in the tree view.
- If a group (folder) is selected, the files within that group will be referenced.

### Options

#### Context Menu

![image004](images/skinWeights_import_export/image004.png)

Right-click on each button in `Quick Mode` or on the tree view in `Advanced Mode` to display the context menu.

- Select Influences
  - Selects the influences contained in the target file.
- Select Geometry
  - Selects the geometry contained in the target file.
- Open Directory
  - Opens the directory where the target file is saved.

#### File Format

![image002](images/skinWeights_import_export/image002.png) ![image003](images/skinWeights_import_export/image003.png)

Select the file format for export in `Advanced Mode`. Click the button to toggle the format.
Choose whether to save the file in binary format (`pickle`) (left) or text format (`json`) (right).
