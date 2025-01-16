# Scene Optimizer

シーンの最適化を行います。

## 使用方法

専用メニューか以下のコマンドで起動します。

```python
import faketools.tools.scene_optimizer
faketools.tools.scene_optimizer.show_ui()
```


![alt text](images/scene_optimizer/image001.png)

各チェックボックスの右のテキストが最適化の内容です。それぞれ個別に実行したい場合は、**RUN** ボタンを押してください。

まとめて実行する場合は、**Optimize Scene** ボタンを押してください。チェックボックスがオンの処理が実行されます。

## 最適化内容

### DataStructure

シーンに存在する DataStructure をすべて削除します。

### UnknownNodes

シーンに存在する unknown ノードをすべて削除します。

### UnusedNodes

シーンに存在する未使用ノードをすべて削除します。

### UnknownPlugins

シーンに存在する unknown プラグインをすべて削除します。

### ScriptNodes

シーンに存在するスクリプトノードをすべて削除します。

### ColorSets

シーンに存在するカラーセットをすべて削除します。

### DisplayLayers

シーンに存在するディスプレイレイヤをすべて削除します。

### TimeAnimCurves

シーンに存在する時間依存のアニメーションカーブをすべて削除します。

### UnusedInfluences

シーンに存在する未使用のインフルエンスをすべて削除します。