from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from ui.components.widgets import label, card, button, Portrait


class SuspectsScreen(QWidget):
    def __init__(self, characters: list[dict], select):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("КРУГ РАССЛЕДОВАНИЯ", "eyebrow"))
        layout.addWidget(label("Подозреваемые", "title"))
        layout.addWidget(label("У каждого своя версия событий. Подозрение не означает виновность.", "muted"))
        grid = QGridLayout()
        grid.setSpacing(16)
        self.profile_buttons = []
        for i, person in enumerate(characters):
            frame, body = card()
            body.addWidget(Portrait(person["initials"]))
            body.addWidget(label(person["name"], "heading"))
            body.addWidget(label(f'{person["role"]} · {person["age"]} лет', "eyebrow"))
            body.addWidget(label(person["character"], "muted"))
            body.addWidget(label(person["bio"]))
            body.addWidget(label(person["public_note"], "muted"))
            btn = button("Открыть досье", lambda checked=False, pid=person["id"]: select(pid), "person")
            self.profile_buttons.append(btn)
            body.addWidget(btn)
            grid.addWidget(frame, i // 2, i % 2)
        layout.addLayout(grid)
