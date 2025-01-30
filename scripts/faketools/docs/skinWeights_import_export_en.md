# SkinWeights Import/Export

This tool allows you to import and export skin weights.

## Overview

You can save skin weights to a file and import them to another geometry. However, you cannot import them to geometry that is already bound.

## Usage

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.tools.skinWeights_import_export_ui
faketools.tools.skinWeights_import_export_ui.show_ui()
```

![image001](images/skinWeights_import_export/image001.png)

### Basic Usage

There are two modes: **Quick Mode** for temporarily saving skin weights and **Advanced Mode** for saving them to a file.

#### Export

1. Select the geometry bound with a skinCluster (multiple selections allowed).

- **Quick Mode**: Press the `Export` button to save the skin weights.
- **Advanced Mode**: Select the file format, enter the group name (folder name) for export, and press the `Export` button to save the skin weights.

#### Import

- **Quick Mode**: Press the `Import` button to load the saved skin weights.
- **Advanced Mode**: Select the group or file to import from the list, and press the `Import` button to load the saved skin weights.

The following cases will prevent import:

- The geometry to import does not exist.
- The influences to import do not exist.
- If the influences to be imported are already bound.

**Selecting Geometry for Import**

- To import to the geometry selected during export, deselect everything before importing. The tool will search the scene for the geometry by name.
- To import to a different geometry than the one selected during export, select the geometry to import before importing.

### Options

#### Context Menu

![image004](images/skinWeights_import_export/image004.png)

Right-click on each button in `Quick Mode` and on the tree view in `Advanced Mode` to display the context menu.

- Select Influences
  - Select the influences contained in the target file.
- Select Geometry
  - Select the geometry contained in the target file.
- Open Directory
  - Open the directory where the data is saved in Explorer.

#### File Format

![image002](images/skinWeights_import_export/image002.png) ![image003](images/skinWeights_import_export/image003.png)

Select the file format for export in `Advanced Mode`. Click the button to switch formats.
Choose whether to save the file in binary format (`pickle`) (left) or text format (`json`) (right).
