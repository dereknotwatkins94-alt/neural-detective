from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QTextEdit, QCheckBox, QMessageBox
from ui.components.widgets import label, card, button


class AccusationScreen(QWidget):
    def __init__(self, engine, changed, draft_changed):
        super().__init__()
        self.engine = engine
        self.changed = changed
        self.draft_changed = draft_changed
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("ФИНАЛЬНОЕ РЕШЕНИЕ", "eyebrow"))
        layout.addWidget(label("Обвинение", "title"))
        layout.addWidget(label("Решение завершит дело и откроет развязку. До подтверждения можно продолжать расследование.", "muted"))
        self.form, body = card()
        self.suspect = QComboBox()
        self.suspect.addItem("Выберите подозреваемого", None)
        for pid, p in engine.people.items():
            self.suspect.addItem(p['name'], pid)
        body.addWidget(self.suspect)
        body.addWidget(label("Приложенные доказательства", "heading"))
        self.checks = {}
        for slot in engine.evidence_slots():
            check = QCheckBox()
            body.addWidget(check)
            self.checks[slot['id']] = check
        self.explanation = QTextEdit()
        self.explanation.setPlaceholderText("Ваша версия событий и связь выбранных доказательств. Текст сохраняется в итоге; автоматическая оценка выполняется по фактам, а не по формулировкам.")
        self.explanation.setMaximumHeight(130)
        body.addWidget(self.explanation)
        body.addWidget(button("Выдвинуть обвинение", self.submit, "scales", True))
        layout.addWidget(self.form)
        self.result_panel, body = card()
        self.result_title = label("", "title")
        self.result_text = label("")
        self.result_text.setTextInteractionFlags(self.result_text.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
        body.addWidget(self.result_title)
        body.addWidget(self.result_text)
        layout.addWidget(self.result_panel)
        layout.addStretch()
        draft = engine.session.accusation_draft
        self.suspect.setCurrentIndex(max(0,self.suspect.findData(draft.get("suspect"))))
        self.explanation.setPlainText(draft.get("explanation",""))
        for eid,check in self.checks.items():
            check.setChecked(eid in draft.get("evidence",[]))
            check.toggled.connect(self.save_draft)
        self.suspect.currentIndexChanged.connect(self.save_draft)
        self.explanation.textChanged.connect(self.save_draft)
        self.refresh()

    def save_draft(self,*_):
        self.engine.session.accusation_draft = {"suspect":self.suspect.currentData(),"explanation":self.explanation.toPlainText(),"evidence":[eid for eid,c in self.checks.items() if c.isChecked()]}
        self.draft_changed()

    def refresh(self):
        result = self.engine.session.result
        self.form.setVisible(result is None)
        self.result_panel.setVisible(result is not None)
        if result:
            self.result_title.setText(result['outcome'])
            names = self.engine.people
            lines = [f"Оценка расследования: {result['score']} / 100", "Вы обвинили: " + names[result['suspect']]['name'],
                     "Шкала: верный выбор — 40; четыре ключевые улики — по 10; подтверждённое противоречие алиби — 20.",
                     "Ваша версия: " + (result['explanation'] or 'не указана'), "", "МОТИВ И РАЗВЯЗКА", result['motive'], "", "ПОСЛЕДОВАТЕЛЬНОСТЬ СОБЫТИЙ", *result['timeline'], "", "РОЛИ ПОДОЗРЕВАЕМЫХ"]
            lines.extend(f"{name}: {role}" for name, role in result['roles'].items())
            lines.extend(["", "ПОЛНОТА МАТЕРИАЛОВ", "Получено: " + (', '.join(result['found']) or 'нет'),
                          "Не получено: " + (', '.join(result['missed']) or 'нет'),
                          "Не хватает в обвинении: " + (', '.join(result['missing_evidence_titles']) or 'все ключевые улики приложены'),
                          "Противоречия: " + ('все необходимые подтверждены' if not result['missing_contradictions'] else 'алиби обвиняемого не сопоставлено с записью на допросе')])
            self.result_text.setText('\n\n'.join(lines))
            return
        for slot in self.engine.evidence_slots():
            check = self.checks[slot['id']]
            check.setText(slot['title'] + (" · изучено" if slot['examined'] else " · требуется изучение"))
            check.setEnabled(slot['examined'])

    def submit(self):
        pid = self.suspect.currentData()
        if pid is None:
            QMessageBox.information(self, "Обвинение", "Выберите подозреваемого.")
            return
        answer = QMessageBox.question(self, "Завершить дело?", "После обвинения откроется развязка. Продолжить расследование в этой сессии будет нельзя. Подтвердить решение?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            selected = [eid for eid, check in self.checks.items() if check.isChecked()]
            self.engine.accuse(pid, selected, self.explanation.toPlainText())
            self.changed()
        except ValueError as error:
            QMessageBox.information(self, "Обвинение", str(error))
