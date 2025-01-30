# Connection Lister

このツールは、ノード間の接続を変更するためのツールです。

## 概要

このツールは、ノード間の接続、値のコピーを行うためのツールです。  
また、用意されたコマンドを使用することで、ノード間に対して特定の操作を行うことができます。

## 使用方法

専用のメニューか、以下のコマンドでツールを起動します。

```python
import faketools.tools.connection_lister_ui
faketools.tools.connection_lister_ui.show_ui()
```

![image001](images/connection_lister/image001.png)

### 基本的な使用方法

ノードやアトリビュートのロード方法は **[Attribute Lister](./attribute_lister.html)** と同様です。  
ノードを選択し、ロードボタンを押すことで、そのノードのアトリビュートがリストに表示されます。

表示されたノードに対して、`Connect` モードで接続と値のコピーを行うことができます。  
また、`Command` モードで、用意されたコマンドを使用することができます。


## Connect モード

値をコピーする場合は、`Copy Value` ボタンを押すことで、そのアトリビュートの値をコピーします。  
アトリビュートを接続する場合は、`Connect` ボタンを押すことで、そのアトリビュートを接続します。

#### ノードとアトリビュートの選択方法

リストに表示されたノードやアトリビュートは、左右で同数のリストを選択するか、

![image003](images/connection_lister/image003.png)

画像のように、ソースとなるノード、アトリビュートが一つで、ターゲットとなるノード、アトリビュートが複数の場合です。

![image004](images/connection_lister/image004.png)

## Command モード

`Command` モードで、用意されたコマンドを使用することができます。

コマンドについては、**Single Command** の **Pair Command** と同様の機能です。  
**[Single Command](./single_commands.html)** のドキュメントを参照してください。

![image002](images/connection_lister/image002.png)



