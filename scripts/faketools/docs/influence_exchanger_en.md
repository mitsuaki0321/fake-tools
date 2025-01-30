# Influence Exchange

Exchange already bound influences with unbound influences.

## How to Use

Use the Skin Weights Utility menu or start the tool with the following command:

```python
import faketools.tools.influence_exchanger_ui
faketools.tools.influence_exchanger_ui.show_ui()
```

![image001](images/influence_exchanger/image001.png)

### Basic Usage

To exchange influences, follow these steps:

1. Select the target skin cluster in `Target SkinClusters` and press the `SET` button.
2. Select the source influences in `Binding Influences` and press the `SET` button. All influences set here must be bound to the skin cluster set in `Target SkinClusters`.
3. Select the target influences in `Exchange Influences` and press the `SET` button. All influences set here must not be bound to the skin cluster set in `Target SkinClusters`.
4. Press the `Exchange Influences` button.