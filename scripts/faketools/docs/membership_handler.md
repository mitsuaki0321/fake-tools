# Transform Creater

デフォーマーのメンバーシップを編集します。コンポーネントタグ設定が有効な場合のみ利用可能です。

WeightGeometryFilter タイプのデフォーマーのみが対象です。

## 使用方法

専用のメニューか、以下のコマンドでツールを起動します。

```python
import faketools.tools.membership_handler
faketools.tools.membership_handler.show_ui()
```

![image001](images/membership_handler/image001.png)

### 起動する条件

このツールは、コンポーネントタグが有効な場合のみ利用可能です。

以下の設定でコンポーネントタグを有効にします。

1. `Preferences` > `Settings` > `Animation` に移動する。
2. `Rigging` セクションの 以下三つの設定をそれぞれ設定する。
    - `Use component tags for deformation component subsets` にチェックを入れる。
    - `Create component tags on deformer creation` にチェックを入れる。
    - `Add tweak nodes on deformer creation` のチェックを外す。

### 基本的な使用方法

1. 編集対象のデフォーマーを選択し、![image001](images/membership_handler/image002.png) ボタンを押します。 
2. そのデフォーマーのメンバーシップにするコンポーネントを選択します。
3. ![image001](images/membership_handler/image003.png) ボタンを押すことで、メンバーシップが更新されます。

![image001](images/membership_handler/image004.png) ボタンを押すことで、対象のデフォーマーに設定されているメンバーシップを選択します。

