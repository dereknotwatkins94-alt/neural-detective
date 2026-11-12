import os
import sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.theme import STYLESHEET


@pytest.fixture(scope="session")
def app():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLESHEET)
    return app


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv("NEURAL_DETECTIVE_HOME",str(tmp_path))
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    window = MainWindow()
    window.show()
    app.processEvents()
    yield window
    window.session.notes = ""
    window.session.started = False
    window.close()
    window.deleteLater()
    app.processEvents()
