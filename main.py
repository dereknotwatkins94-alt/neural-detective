"""Запуск: python main.py из каталога проекта."""
import logging
import os
import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from core.config import AppConfig
from ui.main_window import MainWindow
from ui.theme import STYLESHEET


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    os.environ.setdefault("QT_SCALE_FACTOR", str(AppConfig.load().scale))
    app = QApplication(sys.argv)
    app.setApplicationName("Neural Detective")
    app.setOrganizationName("Neural Detective")
    family = "Segoe UI" if "Segoe UI" in QFontDatabase.families() else app.font().family()
    app.setFont(QFont(family, 11))
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
