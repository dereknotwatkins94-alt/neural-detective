from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox
from ui.components.widgets import label, card, button


class EvidenceScreen(QWidget):
    def __init__(self, engine, changed, present_to):
        super().__init__()
        self.engine = engine
        self.changed = changed
        self.selected = None
        self.present_to = present_to
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("КРИМИНАЛИСТИЧЕСКОЕ ХРАНИЛИЩЕ", "eyebrow"))
        layout.addWidget(label("Улики", "title"))
        self.hint = label("", "muted")
        layout.addWidget(self.hint)
        grid = QGridLayout()
        self.slots = {}
        for i, slot in enumerate(engine.evidence_slots()):
            frame, body = card()
            title = label("", "heading")
            status = label("", "muted")
            action = button("", lambda checked=False, eid=slot["id"]: self.open(eid), "clue")
            body.addWidget(label(f"МАТЕРИАЛ {i + 1:02d}", "eyebrow"))
            body.addWidget(title)
            body.addWidget(status)
            body.addWidget(action)
            self.slots[slot['id']] = (title, status, action)
            grid.addWidget(frame, i // 3, i % 3)
        layout.addLayout(grid)
        frame, body = card()
        self.detail_title = label("Выберите материал", "heading")
        self.detail = label("Сначала запросите доступный материал, затем изучите его. После изучения улику можно предъявить на допросе.")
        self.source = label("", "muted")
        body.addWidget(self.detail_title)
        body.addWidget(self.detail)
        body.addWidget(self.source)
        self.links = QVBoxLayout()
        body.addLayout(self.links)
        layout.addWidget(frame)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        session = self.engine.session
        self.hint.setText(f"Получено {len(session.found)} / 6 · Изучено {len(session.examined)} / 6. Подсказка следующего шага — в обзоре дела.")
        for slot in self.engine.evidence_slots():
            title, status, action = self.slots[slot["id"]]
            title.setText(slot['title'])
            status.setText("Изучено" if slot['examined'] else "Получено · нужно изучить" if slot['found'] else "Можно запросить" if slot['available'] else "Нужно найти основание")
            action.setText("Открыть" if slot['examined'] else "Изучить" if slot['found'] else "Запросить" if slot['available'] else "Пока недоступно")
            action.setEnabled(slot['examined'] or (session.result is None and (slot['found'] or slot['available'])))
        if self.selected:
            self.show_detail(self.selected)

    def open(self, eid):
        try:
            if eid not in self.engine.session.found:
                self.engine.collect(eid)
            else:
                self.engine.examine(eid)
                self.selected = eid
            self.changed()
        except ValueError as error:
            QMessageBox.information(self, "Материалы дела", str(error))

    def show_detail(self, eid):
        detail = self.engine.evidence_detail(eid)
        self.detail_title.setText(detail["title"])
        self.detail.setText(detail["description"])
        names = [self.engine.people[pid]['name'] for pid in detail['related']]
        self.source.setText("Источник: " + detail["source"] + ("\nСвязанные лица: " + ", ".join(names) if names else ""))
        while self.links.count():
            self.links.takeAt(0).widget().deleteLater()
        for pid in detail['related']:
            btn = button("К допросу: " + self.engine.people[pid]['name'], lambda checked=False, p=pid: self.present_to(p, eid), "person")
            self.links.addWidget(btn)
