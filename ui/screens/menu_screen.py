from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPixmap, QLinearGradient, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from core.case_manager import ROOT
from ui.components.widgets import label, button


class MenuScreen(QWidget):
    def __init__(self, new_game, resume, archive, settings, exit_app):
        super().__init__()
        self.background = QPixmap(str(ROOT / "assets/images/office.png"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(68, 44, 60, 28)
        layout.addWidget(label("БЮРО ОСОБЫХ РАССЛЕДОВАНИЙ    /    ТЕРМИНАЛ 01", "eyebrow"))
        layout.addStretch(2)
        brand = label("NEURAL\nDETECTIVE", wrap=False)
        brand.setTextFormat(Qt.TextFormat.RichText)
        brand.setText('NEURAL<br><span style="color: #24B8A8">DETECTIVE</span>')
        brand.setStyleSheet("font-size: 58px; font-weight: 800; color: #E8EDF2;")
        layout.addWidget(brand)
        layout.addWidget(label("Каждая ложь оставляет след", "heading"))
        layout.addSpacing(30)
        self.new_button = button("Новое расследование", new_game, "play", True)
        self.resume_button = button("Продолжить", resume, "resume")
        self.resume_button.setEnabled(False)
        self.resume_button.setToolTip("Нет активной сессии. Постоянные сохранения появятся на этапе 5.")
        self.archive_button = button("Архив дел", archive, "folder")
        self.settings_button = button("Настройки", settings, "settings")
        self.exit_button = button("Выход", exit_app, "power")
        for widget in (self.new_button, self.resume_button, self.archive_button, self.settings_button, self.exit_button):
            widget.setFixedSize(310, 48)
            layout.addWidget(widget)
        layout.addStretch(3)
        layout.addWidget(label("ДЕЛО №001  /  ПОСЛЕДНИЙ ВЕЧЕР", "eyebrow"))
        layout.addWidget(label("Четыре подозреваемых. Один вечер. Слишком много тайн.", "muted"))
        layout.addSpacing(26)
        footer = QHBoxLayout()
        footer.addWidget(label("v1.0.0  ·  Учебный проект", "muted", wrap=False))
        footer.addStretch()
        self.ai_status = label("AI DEMO MODE", "eyebrow", wrap=False)
        footer.addWidget(self.ai_status)
        layout.addLayout(footer)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#080E14"))
        if not self.background.isNull():
            target = QRectF(self.width() * .32, 0, self.width() * .68, self.height())
            scaled = self.background.scaled(int(target.width()), int(target.height()), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(target, scaled, QRectF((scaled.width()-target.width())/2, (scaled.height()-target.height())/2, target.width(), target.height()))
        shade = QLinearGradient(0, 0, self.width(), 0)
        shade.setColorAt(0, QColor("#080E14"))
        shade.setColorAt(.32, QColor("#080E14"))
        shade.setColorAt(.65, QColor(8, 14, 20, 90))
        shade.setColorAt(1, QColor(8, 14, 20, 20))
        painter.fillRect(self.rect(), shade)
