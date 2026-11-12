# Сборка выполняется на целевой ОС: python -m PyInstaller NeuralDetective.spec
from pathlib import Path
root = Path(SPECPATH)
datas = [(str(root/'data'),'data'), (str(root/'assets'),'assets'),
         (str(root/'ml/models'),'ml/models'), (str(root/'ml/dataset.csv'),'ml')]
a = Analysis([str(root/'main.py')], pathex=[str(root)], binaries=[], datas=datas,
    hiddenimports=['google.genai','sklearn.linear_model._logistic','ml.contradiction_model','ml.train_model'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtWebEngineQuick','PySide6.QtQml','PySide6.QtQuick'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='NeuralDetective',debug=False,
          bootloader_ignore_signals=False,strip=False,upx=False,console=False)
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='NeuralDetective')
