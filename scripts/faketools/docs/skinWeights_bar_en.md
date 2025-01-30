# SkinWeights Bar

Performs weight copying and mirroring.

## How to Use

Use the top part of the Skin Weights Utility or start the tool with the following command.

```python
import faketools.tools.skinWeights_bar_ui
faketools.tools.skinWeights_bar_ui.show_ui()
```

![image001](images/skinWeights_bar/image001.png)

### Basic Usage

#### Copy

Performs weight copying.

1. Select the source geometry.
2. Select the target geometry (multiple selections allowed).
3. Press the `COPY` button to copy the weights from the source to the target. If referencing UVs, turn on the `UV` checkbox.

This tool forcibly adds the influences set on the source geometry to the skinCluster of the target geometry.

### Mirror Self

Performs weight mirroring.

1. Select the geometry.
2. Press the `MIR SELF` button to mirror the weights of the selected geometry. Choose the mirroring direction with the arrow buttons. `<-` mirrors from X to -X, and `->` mirrors from -X to X.

This tool searches for the left and right influences set on the selected geometry and forcibly adds the found influences to the skinCluster if the opposite side influences exist.

**Note:** The method for obtaining the opposite side influences in this feature is determined by the settings in `settings.json` for `LEFT_TO_RIGHT` and `RIGHT_TO_LEFT`.

### Mirror Sub

Performs weight mirroring to another geometry.

Example use: Mirroring the weights of a character's left shoe to the right shoe.

1. Select the geometry of the left shoe.
2. Press the `MIR SUB` button. The following steps are executed:
   1. Generate the geometry name of the right shoe from the left shoe's geometry name.
   2. If the right shoe's geometry is found, convert the influence names set on the left shoe's geometry from left to right names.
   3. If the converted influence names exist on the right shoe's geometry, forcibly add those influences to the skinCluster or create a new skinCluster and add them.
   4. Copy the weights set on the left shoe's geometry to the right shoe's geometry.

*Note: The method for searching opposite side geometries or influences is the same as Mirror Self.*
