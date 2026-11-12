"""Журнал, архив и настройки."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QTextBrowser
from ui.components.widgets import label, card, button


def page(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(18)
    layout.addWidget(label("ДЕЛО №001 / ПОСЛЕДНИЙ ВЕЧЕР", "eyebrow"))
    layout.addWidget(label(title, "title"))
    layout.addWidget(label(subtitle, "muted"))
    return widget, layout


class JournalScreen(QWidget):
    def __init__(self, engine, run_task, changed, notes_changed):
        super().__init__()
        self.changed = changed
        self.notes_changed = notes_changed
        self.engine = engine
        self.session = session = engine.session
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("ЛИЧНЫЙ БЛОКНОТ", "eyebrow"))
        layout.addWidget(label("Журнал расследования", "title"))
        layout.addWidget(label("Заметки, показания и результаты анализа автоматически сохраняются в SQLite.", "muted"))
        frame, body = card()
        body.addWidget(label("Заметки детектива", "heading"))
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Что привлекло ваше внимание? Запишите вопросы и первые наблюдения…")
        self.editor.setPlainText(session.notes)
        self.editor.setFixedHeight(200)
        frame.setFixedHeight(280)
        self.editor.textChanged.connect(self.update_notes)
        body.addWidget(self.editor)
        layout.addWidget(frame)
        self.events = QTextBrowser()
        self.events.setMinimumHeight(360)
        layout.addWidget(self.events)
        from ui.screens.ml_panel import MLPanel
        self.ml_panel = MLPanel(engine, run_task, changed)
        layout.addWidget(self.ml_panel)
        self.refresh()

    def refresh(self):
        if hasattr(self,"ml_panel"):
            self.ml_panel.refresh()
        self.events.setPlainText("ЗАПИСИ РАССЛЕДОВАНИЯ\n\n" + ("\n\n".join(self.session.journal) or "Пока нет записей. Показания можно добавить из истории допроса."))

    def update_notes(self):
        self.session.notes = self.editor.toPlainText()
        self.notes_changed()


def archive_screen(start_game, back) -> QWidget:
    widget, layout = page("Архив дел", "Доступно одно дело. Архив подготовлен для расширения.")
    frame, body = card()
    body.addWidget(label("001 / МАТЕРИАЛЫ ДЕЛА", "eyebrow"))
    body.addWidget(label("Последний вечер", "title"))
    body.addWidget(label("Убийство Виктора Орлова. Четыре человека в загородном особняке. Начните с изучения обстоятельств преступления."))
    body.addWidget(button("Начать расследование", start_game, "play", True))
    layout.addWidget(frame)
    layout.addStretch()
    layout.addWidget(button("В главное меню", back, "back"))
    return widget


