"""Локальные настройки. API-ключ не попадает в SQLite или журналы."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import sys
from dotenv import dotenv_values, set_key

from core.case_manager import ROOT


def storage_dir() -> Path:
    override = os.getenv("NEURAL_DETECTIVE_HOME")
    if override:
        return Path(override).expanduser()
    if getattr(sys, "frozen", False):
        base = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".local/share")))
        return base / "NeuralDetective"
    return ROOT / "user_data"


@dataclass
class AppConfig:
    api_key: str = field(default="", repr=False)
    model: str = "gemini-3.1-flash-lite"
    demo: bool = True
    timeout_ms: int = 20000
    scale: float = 1.0

    @classmethod
    def load(cls):
        values = {}
        path = storage_dir() / "settings.json"
        if path.exists():
            try:
                values = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                values = {}
        env = {**dotenv_values(ROOT / ".env"), **dotenv_values(storage_dir() / ".env"), **os.environ}
        try:
            scale = max(0.8,min(1.5,float(values.get("scale",1.0))))
        except (TypeError,ValueError):
            scale = 1.0
        key = env.get("GEMINI_API_KEY", "") or ""
        return cls(api_key=key, model=env.get("GEMINI_MODEL") or values.get("model", cls.model),
                   demo=bool(values.get("demo", not bool(key))),
                   scale=scale)

    def save(self, remember_key: bool = False):
        directory = storage_dir()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "settings.json").write_text(json.dumps({"model": self.model, "demo": self.demo, "scale": self.scale}, ensure_ascii=False, indent=2), encoding="utf-8")
        if remember_key:
            env_path = directory / ".env"
            set_key(str(env_path), "GEMINI_API_KEY", self.api_key)
            env_path.chmod(0o600)
