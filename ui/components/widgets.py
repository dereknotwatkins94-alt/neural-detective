from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QFont, QLinearGradient
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy, QLayout

from core.case_manager import ROOT


def label(text: str, kind: str = "", wrap: bool = True) -> QLabel:
    widget = QLabel(text)
    widget.setProperty("kind", kind)
    widget.setWordWrap(wrap)
    widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


def button(text: str, callback=None, icon: str = "", primary: bool = False) -> QPushButton:
    widget = QPushButton(text)
    widget.setMinimumHeight(42)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setProperty("primary", primary)
    if icon:
        widget.setIcon(QIcon(str(ROOT / "assets/icons" / f"{icon}.svg")))
        widget.setIconSize(QSize(20, 20))
    if callback:
        widget.clicked.connect(callback)
    return widget


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


class Portrait(QWidget):
    """Локальная стилизованная заглушка, заменяемая портретом на следующих этапах."""
    def __init__(self, initials: str, parent=None):
        super().__init__(parent)
        self.initials = initials
        self.setMinimumHeight(145)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#203D46"))
        gradient.setColorAt(1, QColor("#0C151D"))
        painter.setBrush(gradient)
        painter.setPen(QColor("#34515B"))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        painter.setPen(QColor("#304C55"))
        for x in range(20, self.width(), 28):
            painter.drawLine(x, 0, x, self.height())
        painter.setPen(QColor("#9AB9BC"))
        painter.setFont(QFont(self.font().family(), 34, QFont.Weight.Light))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.initials)
        painter.setFont(QFont(self.font().family(), 8))
        painter.setPen(QColor("#78939D"))
        painter.drawText(self.rect().adjusted(12, 0, -12, -12), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, "ФОТО НЕТ")
