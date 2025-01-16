# SkinWeights Import/Export

スキンウェイトのインポート、エクスポートを行うツールです。


## 使用方法

専用のメニューか、以下のコマンドでツールを起動します。

```python
import faketools.tools.skinWeights_import_export
faketools.tools.skinWeights_import_export.show_ui()
```

![image001](images/skinWeights_import_export/image001.png)

### 基本的な使用方法

一時的にスキンウエイトを保存する場合の Quick Mode と、ファイルに保存する場合の Advanced Mode があります。

#### Quick Mode

**Export**

1. ジオメトリを選択します。
2. `Export` ボタンを押して、スキンウエイトを保存します。この時、ウエイトは各OSのテンポラリディレクトリに保存されます。

**Import**

1. `Import` ボタンを押して、保存したスキンウエイトを読み込みます。

#### Advanced Mode

**Export**

1. ジオメトリを選択します。
2. ファイルフォーマットを `json` か `pickle` から選択します。
3. エクスポートするグループ名（フォルダ名）を入力します。
4. `Export` ボタンを押して、スキンウエイトを保存します。

**Import**

1. ツリービューからインポートするグループかファイルを選択します。
2. `Import` ボタンを押して、保存したスキンウエイトを読み込みます。

#### Import について

- ジオメトリを選択していた場合は、そのジオメトリの個数とツリービューで選択しているファイルの個数が一致している必要があります。
- グループ（フォルダ）を選択している場合は、そのグループ内のファイルを参照します。

### オプション

#### コンテキストメニュー

![image004](images/skinWeights_import_export/image004.png)

`Quick Mode` の各ボタン上と、`Advanced Mode` の ツリービュー上で右クリックすると、コンテキストメニューが表示されます。

- Select Influences
  - 対象ファイル内に含まれるインフルエンスを選択します。
- Select Geometry
  - 対象ファイル内に含まれるジオメトリを選択します。
- Open Directory
  - 対象ファイルが保存されているディレクトリを開きます。

#### ファイルフォーマット

![image002](images/skinWeights_import_export/image002.png) ![image003](images/skinWeights_import_export/image003.png)

`Advanced Mode` でエクスポートする際のファイルフォーマットを選択します。ボタンを選択すると、フォーマットが切り替わります。
ファイルを バイナリ形式 (`pickle`) ( 左 ) で保存するか、テキスト形式 (`json`) ( 右 ) で保存するかを選択します。


