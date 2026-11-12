"""Создать переносимый архив исходников без ключей, окружения и сохранений."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
output=root/'dist/neural-detective-source.zip'
output.parent.mkdir(exist_ok=True)
excluded={'.venv','user_data','__pycache__','.pytest_cache','build','dist','.git'}
with ZipFile(output,'w',ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if (path.is_file() and not excluded.intersection(relative.parts)
                and path.name!='.env' and path.suffix not in {'.db','.log','.pyc'}):
            archive.write(path,Path('neural_detective')/relative)
print(output)
