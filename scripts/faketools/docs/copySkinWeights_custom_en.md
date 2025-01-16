# Copy SkinWeights Custom

Copy weights with specified options.

## How to Use

Use the Skin Weights Utility menu or start the tool with the following command:

```python
import faketools.tools.skinWeights_copy_custom
faketools.tools.skinWeights_copy_custom.show_ui()
```

![image001](images/skinWeights_copy_custom/image001.png)

### Basic Usage

To copy weights, follow these steps:

1. Select the source geometry.
2. Select the target geometry (multiple selections allowed).
3. Choose the copy method and press the `Copy Skin Weights` button.

### Options

- **Blend**
  - Copy weights at the specified ratio.
- **Use Only Unlocked Influences**
  - Use only unlocked influences for copying.
- **Reference Original Shape**
  - Reference the original shape (Intermediate Object) for copying.
- **Add Missing Influence**
  - Automatically add missing influences to the target during copying.
