from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar
from ui.components.widgets import label, card, Portrait


class CaseScreen(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        case = engine.case
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(label("МАТЕРИАЛЫ РАССЛЕДОВАНИЯ", "eyebrow"))
        layout.addWidget(label("Последний вечер", "title"))
        row = QHBoxLayout()
        main, info = card()
        inside = QHBoxLayout()
        portrait = Portrait("ВО")
        portrait.setFixedWidth(135)
        inside.addWidget(portrait)
        details = QVBoxLayout()
        details.addWidget(label("Виктор Орлов", "heading"))
        details.addWidget(label("ПОГИБШИЙ / ПРЕДПРИНИМАТЕЛЬ", "eyebrow"))
        details.addWidget(label(case["description"]))
        inside.addLayout(details, 1)
        info.addLayout(inside)
        row.addWidget(main, 3)
        stats, body = card()
        body.addWidget(label("Полнота исследования", "heading"))
        self.stats = label("", "muted")
        body.addWidget(self.stats)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        body.addWidget(self.progress)
        row.addWidget(stats, 1)
        layout.addLayout(row)
        facts = QHBoxLayout()
        for name, value in (("ДАТА", case["date"]), ("МЕСТО", case["location"]), ("ПРЕДВАРИТЕЛЬНОЕ ВРЕМЯ СМЕРТИ", case["death_window"])):
            frame, body = card()
            body.addWidget(label(name, "muted"))
            body.addWidget(label(value, "heading"))
            facts.addWidget(frame)
        layout.addLayout(facts)
        self.hint = label("", "eyebrow")
        layout.addWidget(self.hint)
        frame, body = card()
        body.addWidget(label("Хронология известных событий", "heading"))
        self.timeline_label = label("")
        body.addWidget(self.timeline_label)
        layout.addWidget(frame)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        stats = self.engine.statistics()
        self.stats.setText(f"Улики: {stats['examined']} / 6\nДопросы: {stats['interviewed']} / 4\nПротиворечия: {stats['contradictions']}\nИсследовано: {stats['progress']}%")
        self.progress.setValue(stats['progress'])
        self.hint.setText("Дело завершено. Итог доступен в разделе «Обвинение»." if self.engine.session.result else self.engine.hints())
        self.timeline_label.setText("\n\n".join(f"{e['time']}  /  {e['title']}\n{e['description']}" for e in self.engine.timeline()))
