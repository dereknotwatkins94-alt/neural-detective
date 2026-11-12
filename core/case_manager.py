"""Загрузка локальных ресурсов, в том числе из сборки PyInstaller."""
import json
from pathlib import Path
import sys

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def load_case() -> dict:
    return json.loads((ROOT / "data/case_001.json").read_text(encoding="utf-8"))


def load_characters() -> list[dict]:
    return json.loads((ROOT / "data/characters.json").read_text(encoding="utf-8"))
