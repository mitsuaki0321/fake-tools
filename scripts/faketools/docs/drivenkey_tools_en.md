# DrivenKey Tools

This tool assists in editing set driven keys.

## Overview

This tool assists in editing set driven keys.

It mainly provides the following functions for set driven keys:

- Save and Load
- Copy and Paste
- Mirror Animation Curves
- Several Utility Functions

## Usage

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.tools.drivenkey_tools
faketools.tools.drivenkey_tools.show_ui()
```

![image001](images/drivenkey_tools/image001.png)

### Save and Load Set Driven Keys

Save set driven keys to a file and reproduce them from the saved file.  
There are **Quick** mode and **Advanced** mode.

![image002](images/drivenkey_tools/image002.png)

To save set driven keys to a file, follow these steps:

1. Select the nodes with set driven keys (multiple selections allowed).

2. Press the **Export** button to save the data.
   1. In **Quick** mode, the file is temporarily saved in the TEMP folder.
   2. In **Advanced** mode, the file is saved to a specified location. Enter the file name and press the `Save` button.

To load set driven keys from a file, follow these steps:

1. Press the **Import** button to load the saved file.
   1. In **Quick** mode, the file saved in the TEMP folder is loaded.
   2. In **Advanced** mode, select the file to load and press the `Open` button.

2. The set driven keys saved in the file are reproduced, and the target nodes are selected.

### Copy and Paste Set Driven Keys

Copy and paste set driven keys.  
There are two methods: **One to All** and **One to Replace**.

![image003](images/drivenkey_tools/image003.png)

#### One to All

Copy the set driven keys from one node to multiple nodes.

To copy, follow these steps:

1. Select the source node.
2. Add the target nodes (multiple selections allowed).
3. Press the `One to All` button.

#### One to Replace

Copy the set driven keys from one node to nodes found in the scene by replacing the node name.  
Use the field below the `One to Replace` button for node name replacement (replaced with Python regular expressions).

To copy, follow these steps:

1. Select the source node (multiple selections allowed).
2. Press the `One to Replace` button. The target nodes are found in the scene and copied.

- **Replace Driver**
  - Use the replaced driver node name.
- **Force Delete Driven Key**
  - If the target node already has set driven keys, delete all driven keys except the applied ones and copy.
- **Mirror**
   - Mirror the T (Translate), R (Rotate), and S (Scale) animation curves of the target node in the **Time** or **Value** direction.

### Mirror Animation Curves

Mirror animation curves.

![image004](images/drivenkey_tools/image004.png)

To mirror, follow these steps:

1. Select the driven key animation curves to mirror (multiple selections allowed).
2. Press the `Time` or `Value` button.
   - Press the `Time` button to mirror the animation curves in the time direction.
   - Press the `Value` button to mirror the animation curves in the value direction.

### Options

There are several additional functions.

![image005](images/drivenkey_tools/image005.png)

- **Select Driven Key Nodes**
  - Select nodes with set driven keys.
    - If nodes are already selected in the scene, select the nodes with set driven keys within those nodes.
    - If nothing is selected, select all nodes with set driven keys in the scene.
- **Cleanup Driven Key**
   - Clean up nodes with set driven keys. Organize the following situations:
     - Delete driven keys with no driver.
     - Delete driven keys where all values are the same and all tangent values are 0.0.
     - If the above conditions are met and after deletion, if the blendWeighted node has no animCurve connected or only one connected, delete the blendWeighted node.
     - Clean up thoroughly.
