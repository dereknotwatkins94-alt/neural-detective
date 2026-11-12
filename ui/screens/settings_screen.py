from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox
from ui.components.widgets import label, card, button


class SettingsScreen(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32,24,32,24)
        layout.addWidget(label('Настройки','title'))
        layout.addWidget(label('NEURAL DETECTIVE / версия 1.0.0','eyebrow'))
        frame,body = card()
        body.addWidget(label('Подключение Gemini','heading'))
        self.status = label(window.ai_status,'eyebrow')
        body.addWidget(self.status)
        self.demo = QCheckBox('Деморежим: локальные ответы без сети')
        self.demo.setChecked(window.config.demo)
        body.addWidget(self.demo)
        body.addWidget(label('API-ключ (также читается из GEMINI_API_KEY или .env)','muted'))
        self.key = QLineEdit(window.config.api_key)
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        body.addWidget(self.key)
        self.remember = QCheckBox('Сохранить ключ локально в user_data/.env')
        body.addWidget(self.remember)
        body.addWidget(label('Идентификатор модели Gemini','muted'))
        self.model = QLineEdit(window.config.model)
        body.addWidget(self.model)
        body.addWidget(button('Применить настройки',window.apply_settings,'settings',True))
        body.addWidget(button('Проверить подключение',window.check_connection,'resume'))
        body.addWidget(label('В AI DEMO MODE ответы написаны заранее. При подключении Gemini выбирает подходящий ответ и его подачу в пределах разрешённых фактов. Ключ не хранится в SQLite.','muted'))
        layout.addWidget(frame)
        frame,body = card()
        body.addWidget(label('Масштаб интерфейса','heading'))
        self.scale = QComboBox()
        for value in (0.9,1.0,1.1,1.25):
            self.scale.addItem(f'{round(value*100)}%',value)
        self.scale.setCurrentIndex(max(0,self.scale.findData(window.config.scale)))
        body.addWidget(self.scale)
        body.addWidget(label('Масштаб применяется после перезапуска. Звуки интерфейса не используются.','muted'))
        layout.addWidget(frame)
        layout.addWidget(button('В главное меню',window.show_menu,'back'))
        layout.addStretch()
