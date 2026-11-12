from html import escape
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QProgressBar, QTextBrowser, QMessageBox, QLineEdit
from ui.components.widgets import label, card, button, Portrait


class InterrogationScreen(QWidget):
    def __init__(self, characters: list[dict], engine, changed, send_dialogue):
        super().__init__()
        self.characters = characters
        self.engine = engine
        self.session = engine.session
        self.changed = changed
        self.send_dialogue = send_dialogue
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("КОМНАТА ДОПРОСА", "eyebrow"))
        layout.addWidget(label("Показания и противоречия", "title"))
        self.selector = QComboBox()
        for p in characters:
            self.selector.addItem(p["name"], p["id"])
        self.selector.currentIndexChanged.connect(self.update_person)
        layout.addWidget(self.selector)
        row = QHBoxLayout()
        self.profile, body = card()
        self.profile.setFixedWidth(235)
        self.portrait = Portrait("")
        self.name = label("", "heading")
        self.role = label("", "muted")
        self.status = label("", "eyebrow")
        for widget in (self.portrait, self.name, self.role, self.status):
            body.addWidget(widget)
        self.meters = []
        for title in ("Доверие", "Стресс"):
            title_label = label(title, "muted")
            body.addWidget(title_label)
            bar = QProgressBar()
            bar.setTextVisible(False)
            if title == "Стресс":
                bar.setObjectName("stress")
            body.addWidget(bar)
            self.meters.append((title_label, bar))
        body.addStretch()
        body.addWidget(label("Задайте свой вопрос или выберите предложенный. Источник каждого ответа указан в истории.", "muted"))
        row.addWidget(self.profile)
        chat, body = card()
        self.history = QTextBrowser()
        self.history.setOpenLinks(False)
        self.history.setMinimumHeight(235)
        self.history.anchorClicked.connect(self.pin_message)
        body.addWidget(self.history, 1)
        free_row = QHBoxLayout()
        self.free_question = QLineEdit()
        self.free_question.setMaxLength(2000)
        self.free_question.setPlaceholderText("Введите любой вопрос на русском…")
        self.free_question.returnPressed.connect(self.send_free)
        self.free_button = button("Отправить", self.send_free, "play", True)
        free_row.addWidget(self.free_question,1)
        free_row.addWidget(self.free_button)
        body.addLayout(free_row)
        self.question = QComboBox()
        body.addWidget(self.question)
        actions = QHBoxLayout()
        self.tone = QComboBox()
        self.tone.addItem("Спокойно", "calm")
        self.tone.addItem("С нажимом", "pressure")
        actions.addWidget(self.tone)
        self.ask_button = button("Задать вопрос", self.ask, "person", True)
        actions.addWidget(self.ask_button)
        body.addLayout(actions)
        evidence = QHBoxLayout()
        self.evidence = QComboBox()
        evidence.addWidget(self.evidence, 1)
        self.present_button = button("Предъявить улику", self.present, "clue")
        evidence.addWidget(self.present_button)
        body.addLayout(evidence)
        row.addWidget(chat, 1)
        layout.addLayout(row, 1)
        self.select(self.session.suspect_id)

    def select(self, pid: str):
        self.selector.setCurrentIndex(max(0, self.selector.findData(pid)))
        self.update_person()

    def update_person(self, *_):
        pid = self.selector.currentData()
        self.session.suspect_id = pid
        previous = self.question.currentData()
        self.question.clear()
        for q in self.engine.questions(pid):
            self.question.addItem(q["text"], q["id"])
        self.question.setCurrentIndex(max(0, self.question.findData(previous)))
        self.refresh()

    def refresh(self):
        pid = self.selector.currentData()
        p = next(p for p in self.characters if p["id"] == pid)
        state = self.session.characters[pid]
        self.portrait.initials = p["initials"]
        self.portrait.update()
        self.name.setText(p["name"])
        self.role.setText(p["role"])
        self.status.setText("Показания уточнены" if state.secret_revealed else "Допрос идёт" if self.session.dialogues[pid] else "Ещё не опрошен")
        for (title, bar), value, name in zip(self.meters, (state.trust, state.stress), ("Доверие", "Стресс")):
            title.setText(f"{name} · {value}%")
            bar.setValue(value)
        parts = []
        for index, msg in enumerate(self.session.dialogues[pid]):
            detective = msg.speaker == "detective"
            who = "Детектив" if detective else p["name"] + (" / " + msg.source if msg.source else " / Сценарий")
            align = "right" if detective else "left"
            color = "#12413F" if detective else "#192630"
            pin = ""
            if not detective:
                pin = " · В журнале" if (pid, index) in self.session.pinned else f' · <a href="pin:{index}" style="color:#24B8A8">В журнал</a>'
            parts.append(f'<table width="100%"><tr><td align="{align}" bgcolor="{color}" style="padding:10px"><span style="color:#8D9AA8">{escape(who)} · {escape(msg.time)}{pin}</span><br>{escape(msg.text)}</td></tr></table><br>')
        self.history.setHtml(''.join(parts) or '<p style="color:#8D9AA8">Выберите вопрос, чтобы начать допрос.</p>')
        self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())
        selected = self.evidence.currentData()
        self.evidence.clear()
        for slot in self.engine.evidence_slots():
            if slot["examined"]:
                self.evidence.addItem(slot["title"], slot["id"])
        self.evidence.setCurrentIndex(max(0, self.evidence.findData(selected)))
        active = self.session.result is None
        self.free_button.setEnabled(active)
        self.free_question.setEnabled(active)
        self.ask_button.setEnabled(active)
        self.present_button.setEnabled(active and bool(self.session.examined))
        self.tone.setEnabled(active)

    def _perform(self, action):
        try:
            action()
            self.changed()
        except ValueError as error:
            QMessageBox.information(self, "Допрос", str(error))

    def ask(self):
        self._perform(lambda: self.send_dialogue(self.selector.currentData(), self.question.currentText(), self.tone.currentData(), self.question.currentData()))

    def present(self):
        if not self.evidence.currentData():
            return
        title = "Предъявлена улика: " + self.evidence.currentText()
        self._perform(lambda: self.send_dialogue(self.selector.currentData(), title, self.tone.currentData(), evidence_id=self.evidence.currentData()))

    def send_free(self):
        question = self.free_question.text().strip()
        if question:
            self._perform(lambda: self.send_dialogue(self.selector.currentData(), question, self.tone.currentData()))
            self.free_question.clear()

    def pin_message(self, url):
        try:
            if url.scheme() != "pin":
                return
            index = int(url.path())
        except ValueError:
            return
        self._perform(lambda: self.engine.pin(self.selector.currentData(), index))
