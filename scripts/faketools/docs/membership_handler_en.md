# Transform Creator

Edit the membership of deformers. Available only when component tag settings are enabled.

Only deformers of the WeightGeometryFilter type are targeted.

## How to Use

Launch the tool from the dedicated menu or with the following command:

```python
import faketools.tools.membership_handler_ui
faketools.tools.membership_handler_ui.show_ui()
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

1. Select the deformer to edit and press the ![image002](images/membership_handler/image002.png) button.  
![image006](images/membership_handler/image006.png)  
*Note: In the image, the handle of the cluster deformer is selected, but in reality, select the deformer itself and press the button.*

1. The name of the selected deformer will be displayed in the middle field.  
![image005](images/membership_handler/image005.png)

1. Press the ![image004](images/membership_handler/image004.png) button to select the membership registered to that deformer.  
![image007](images/membership_handler/image007.png)

1. Select the components you want to update and press the ![image001](images/membership_handler/image003.png) button to update the membership.  
![image008](images/membership_handler/image008.png)
