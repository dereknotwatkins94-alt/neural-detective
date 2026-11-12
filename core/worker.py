"""Сетевые и ML-задачи выполняются вне потока GUI."""
import logging
from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            self.completed.emit(self.operation())
        except Exception as error:
            # Текст исключения SDK может содержать детали запроса: не пишем его в лог.
            logging.warning("Фоновая операция завершилась ошибкой: %s", type(error).__name__)
            self.failed.emit("Не удалось выполнить операцию. Проверьте настройки и повторите попытку.")
