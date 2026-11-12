from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from core.config import storage_dir
from core.game_engine import GameSession, Message
from core.character_state import CharacterState
from database.db_manager import Database


class SaveError(Exception):
    """Ошибка сохранения с безопасным сообщением для пользователя."""


class SaveManager:
    VERSION = 1

    def __init__(self, path: Path | None = None):
        self.db = Database(path or storage_dir() / "investigation.db")

    def exists(self) -> bool:
        if not self.db.path.exists():
            return False
        try:
            with self.db.connect() as connection:
                return connection.execute("SELECT 1 FROM saves WHERE slot=1").fetchone() is not None
        except (OSError, sqlite3.Error) as error:
            raise SaveError("Не удалось прочитать базу сохранений.") from error

    def save(self, session: GameSession):
        if not session.started:
            return
        data = asdict(session)
        for key in ("found", "examined", "asked", "contradictions"):
            data[key] = sorted(data[key])
        data['pinned'] = [list(item) for item in sorted(session.pinned)]
        for state in data['characters'].values():
            state['presented'] = sorted(state['presented'])
        try:
            payload = json.dumps(data, ensure_ascii=False)
            with self.db.connect() as connection:
                connection.execute("INSERT INTO saves VALUES(1, ?, '001', ?, strftime('%Y-%m-%dT%H:%M:%SZ','now')) ON CONFLICT(slot) DO UPDATE SET version=excluded.version, case_id=excluded.case_id, payload=excluded.payload, updated_at=excluded.updated_at", (self.VERSION, payload))
        except (OSError, sqlite3.Error) as error:
            raise SaveError("Не удалось сохранить прогресс. Проверьте доступ к папке user_data.") from error

    def load(self) -> GameSession:
        try:
            with self.db.connect() as connection:
                row = connection.execute("SELECT version, case_id, payload FROM saves WHERE slot=1").fetchone()
            if row is None:
                raise SaveError("Сохранённое расследование не найдено.")
            if row[0] != self.VERSION or row[1] != '001':
                raise SaveError("Эта версия сохранения не поддерживается.")
            data = json.loads(row[2])
            for key in ("found", "examined", "asked", "contradictions"):
                data[key] = set(data[key])
            data['pinned'] = {tuple(item) for item in data['pinned']}
            data['characters'] = {pid: CharacterState(**{**state, 'presented': set(state['presented'])}) for pid, state in data['characters'].items()}
            data['dialogues'] = {pid: [Message(**m) for m in messages] for pid, messages in data['dialogues'].items()}
            session = GameSession(**data)
            self._validate(session)
            return session
        except SaveError:
            raise
        except (OSError, sqlite3.Error, TypeError, ValueError, KeyError, AttributeError) as error:
            raise SaveError("Сохранение повреждено или имеет неподдерживаемый формат. Исходный файл не изменён.") from error

    @staticmethod
    def _validate(session: GameSession):
        from core.game_engine import GameEngine
        engine = GameEngine(session)
        people = set(engine.people)
        evidence = {slot['id'] for slot in engine.evidence_slots()}
        if (not session.started or set(session.characters) != people or set(session.dialogues) != people
                or session.suspect_id not in people or not session.examined <= session.found <= evidence
                or not isinstance(session.notes, str) or not all(isinstance(s, str) for s in session.journal)):
            raise ValueError("Invalid session")
        for state in session.characters.values():
            if not (0 <= state.trust <= 100 and 0 <= state.stress <= 100 and state.presented <= session.examined):
                raise ValueError("Invalid character state")
