# fake-tools

![Maya2023](https://img.shields.io/badge/Maya-2023-blue?&logo=Autodesk)
![NumPy](https://img.shields.io/badge/NumPy-2.0.2-blue?&logo=NumPy)
![SciPy](https://img.shields.io/badge/SciPy-1.13.1-blue?&logo=SciPy)

## Overview

Maya での作業を効率化するための個人用ツール集です。  

This is a collection of personal tools to streamline work in Maya.

## Installation

- faketools.mod を MAYA_MODULE_PATH に追加してください。
- NumPy と SciPy が必要です。NumPy and SciPy are required.


- Add faketools.mod to MAYA_MODULE_PATH.
- NumPy and SciPy are required.

## Launch menu

以下コマンドで、Maya のメインメニューに `FakeTools` メニューが追加されます。  

The `FakeTools` menu is added to the main menu of Maya with the following command.


```python
import faketools.menu
faketools.menu.add_menu()
```

ツールのヘルプは、追加されるメニューの最下部からアクセスできます。

Tool help can be accessed from the bottom of the added menu.