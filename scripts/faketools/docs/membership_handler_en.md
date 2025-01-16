# Transform Creator

Edit the membership of deformers. Available only when component tag settings are enabled.

Only deformers of the WeightGeometryFilter type are targeted.

## How to Use

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.tools.membership_handler
faketools.tools.membership_handler.show_ui()
```

![image001](images/membership_handler/image001.png)

### Conditions for Launch

This tool is available only when component tags are enabled.

Enable component tags with the following settings:

1. Navigate to `Preferences` > `Settings` > `Animation`.
2. In the `Rigging` section, configure the following three settings:
    - Check `Use component tags for deformation component subsets`.
    - Check `Create component tags on deformer creation`.
    - Uncheck `Add tweak nodes on deformer creation`.

### Basic Usage

1. Select the deformer to edit and press the ![image001](images/membership_handler/image002.png) button.
2. Select the components to be included in the deformer’s membership.
3. Press the ![image001](images/membership_handler/image003.png) button to update the membership.

Press the ![image001](images/membership_handler/image004.png) button to select the membership set for the target deformer.

