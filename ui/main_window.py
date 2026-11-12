from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QScrollArea, QFrame, QMessageBox, QButtonGroup, QLayout, QProgressBar,
)

from core.case_manager import load_case, load_characters
from core.game_engine import GameSession, GameEngine
from ui.components.widgets import label, button
from ui.screens.menu_screen import MenuScreen
from ui.screens.case_screen import CaseScreen
from ui.screens.suspects_screen import SuspectsScreen
from ui.screens.interrogation_screen import InterrogationScreen
from ui.screens.workspace_screens import (
    JournalScreen, archive_screen,
)

from ui.screens.settings_screen import SettingsScreen
from core.config import AppConfig
from core.save_manager import SaveManager, SaveError
from core.worker import Worker
from ai.character_agent import CharacterAgent
from ai.api_client import GeminiProvider
from ui.screens.evidence_screen import EvidenceScreen
from ui.screens.accusation_screen import AccusationScreen

SECTIONS = (
    ("Обзор дела", "home"), ("Подозреваемые", "people"), ("Допрос", "person"),
    ("Улики", "clue"), ("Журнал расследования", "journal"), ("Обвинение", "scales"),
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neural Detective — Дело №001: Последний вечер")
        self.resize(1280, 800)
        self.setMinimumSize(1080, 680)
        self.config = AppConfig.load()
        self.save_manager = SaveManager()
        self._worker = None
        self.ai_status = "AI DEMO MODE" if self.config.demo or not self.config.api_key else "GEMINI: НЕ ПРОВЕРЕНО"
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save_game)
        self.session = GameSession()
        self.case = load_case()
        self.characters = load_characters()
        self.root = QStackedWidget()
        self.setCentralWidget(self.root)
        self.menu = MenuScreen(self.start_new, self.resume, self.show_archive, self.show_settings, self.close)
        self.root.addWidget(self.menu)
        self.archive = self._scroll(archive_screen(self.start_new, self.show_menu))
        self.settings_screen = SettingsScreen(self)
        self.settings = self._scroll(self.settings_screen)
        self.root.addWidget(self.archive)
        self.root.addWidget(self.settings)
        self.workspace = None
        self.activity = QProgressBar()
        self.activity.setRange(0,0)
        self.activity.setFixedWidth(100)
        self.statusBar().addPermanentWidget(self.activity)
        self.activity.hide()
        self.update_menu()

    @staticmethod
    def _scroll(content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        return scroll

    def start_new(self):
        if self.is_busy():
            return
        if self.session.started or self.save_exists():
            answer = QMessageBox.question(
                self, "Новое расследование", "Начать заново? Предыдущее сохранение этого дела будет заменено.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.session.start_new()
        self.engine = GameEngine(self.session)
        self._build_workspace()
        self.menu.resume_button.setEnabled(True)
        self.menu.resume_button.setToolTip("Загрузить сохранённое расследование.")
        self.save_game()
        self.resume()

    def _build_workspace(self):
        if self.workspace is not None:
            self.root.removeWidget(self.workspace)
            self.workspace.deleteLater()
        self.workspace = QWidget()
        outer = QHBoxLayout(self.workspace)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(14, 30, 14, 24)
        brand = label("NEURAL\nDETECTIVE", "heading")
        brand.setStyleSheet("color: #47D5C6; font-size: 23px; font-weight: 800;")
        nav.addWidget(brand)
        self.case_badge = label("ДЕЛО №001 / АКТИВНО", "muted")
        nav.addWidget(self.case_badge)
        nav.addSpacing(32)
        self.nav_buttons = {}
        group = QButtonGroup(self.workspace)
        group.setExclusive(True)
        for section, icon in SECTIONS:
            display_name = "Журнал" if section == "Журнал расследования" else section
            btn = button(display_name, lambda checked=False, name=section: self.navigate(name), icon)
            btn.setProperty("nav", True)
            btn.setCheckable(True)
            group.addButton(btn)
            self.nav_buttons[section] = btn
            nav.addWidget(btn)
        nav.addStretch()
        self.mode_label = label(self.ai_status,"eyebrow")
        nav.addWidget(self.mode_label)
        nav.addWidget(button("В главное меню", self.show_menu, "back"))
        outer.addWidget(sidebar)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        header = QHBoxLayout(topbar)
        header.setContentsMargins(24, 16, 24, 16)
        header.addWidget(label("ДЕЛО №001 — ПОСЛЕДНИЙ ВЕЧЕР", "heading"), 1)
        self.evidence_count = label("Улики: 0 / 6", "eyebrow")
        header.addWidget(self.evidence_count)
        header.addSpacing(14)
        save = button("Сохранить", lambda: self.save_game(True), icon="save")
        save.setToolTip("Сохранить весь прогресс в SQLite.")
        header.addWidget(save)
        right.addWidget(topbar)
        strip = QHBoxLayout()
        strip.setContentsMargins(26, 12, 26, 6)
        self.section_label = label("Обзор дела", "muted")
        strip.addWidget(self.section_label)
        strip.addStretch()
        self.api_label = label(self.ai_status,"eyebrow",wrap=False)
        strip.addWidget(self.api_label)
        right.addLayout(strip)
        self.pages = QStackedWidget()
        self.interrogation = InterrogationScreen(self.characters, self.engine, self.refresh_state, self.send_dialogue)
        self.journal = JournalScreen(self.engine, self.run_task, self.refresh_state, self.schedule_save)
        self.overview = CaseScreen(self.engine)
        self.evidence_screen = EvidenceScreen(self.engine, self.refresh_state, self.prepare_evidence)
        self.accusation = AccusationScreen(self.engine, self.refresh_state, self.schedule_save)
        screens = [self.overview, SuspectsScreen(self.characters, self.select_suspect),
                   self.interrogation, self.evidence_screen, self.journal, self.accusation]
        for screen in screens:
            container = QWidget()
            margin = QVBoxLayout(container)
            margin.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
            margin.setContentsMargins(26, 18, 26, 24)
            margin.addWidget(screen)
            self.pages.addWidget(self._scroll(container))
        right.addWidget(self.pages, 1)
        outer.addLayout(right, 1)
        self.root.addWidget(self.workspace)
        self.navigate("Обзор дела")

    def refresh_state(self):
        for screen in (self.overview, self.interrogation, self.evidence_screen, self.journal, self.accusation):
            screen.refresh()
        self.evidence_count.setText(f"Улики: {len(self.session.found)} / 6")
        self.case_badge.setText("ДЕЛО №001 / ЗАВЕРШЕНО" if self.session.result else "ДЕЛО №001 / АКТИВНО")
        self.schedule_save()

    def prepare_evidence(self, pid: str, eid: str):
        self.select_suspect(pid)
        self.interrogation.evidence.setCurrentIndex(self.interrogation.evidence.findData(eid))

    def navigate(self, name: str):
        index = [item[0] for item in SECTIONS].index(name)
        self.pages.setCurrentIndex(index)
        self.nav_buttons[name].setChecked(True)
        self.section_label.setText(name)
        self.session.section = name
        self.refresh_state()

    def select_suspect(self, pid: str):
        self.interrogation.select(pid)
        self.navigate("Допрос")

    def resume(self):
        if self.is_busy():
            return
        if not self.session.started:
            try:
                self.session = self.save_manager.load()
                self.engine = GameEngine(self.session)
                section = self.session.section
                self._build_workspace()
                self.session.section = section if section in dict(SECTIONS) else "Обзор дела"
                self.interrogation.select(self.session.suspect_id)
            except SaveError as error:
                QMessageBox.information(self,"Сохранение",str(error))
                return
        if self.session.started and self.workspace is not None:
            self.root.setCurrentWidget(self.workspace)
            self.navigate(self.session.section)

    def show_menu(self):
        self.root.setCurrentWidget(self.menu)

    def show_archive(self):
        self.root.setCurrentWidget(self.archive)

    def show_settings(self):
        self.root.setCurrentWidget(self.settings)

    def closeEvent(self, event):
        if self.is_busy():
            self.statusBar().showMessage("Дождитесь завершения операции перед выходом.",5000)
            event.ignore()
            return
        self.autosave_timer.stop()
        if self.session.started and not self.save_game():
            answer = QMessageBox.question(self,"Выйти без сохранения?","Сохранение не удалось. Выйти и потерять последние изменения?",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def is_busy(self):
        return self._worker is not None

    def schedule_save(self):
        if self.session.started:
            self.autosave_timer.start(450)

    def save_exists(self):
        try:
            return self.save_manager.exists()
        except SaveError as error:
            self.statusBar().showMessage(str(error),8000)
            return False

    def update_menu(self):
        self.menu.resume_button.setEnabled(self.session.started or self.save_exists())
        self.menu.resume_button.setToolTip("Загрузить последнее сохранение SQLite.")
        self.menu.ai_status.setText(self.ai_status)

    def save_game(self, notify=False):
        self.autosave_timer.stop()
        try:
            self.save_manager.save(self.session)
            self.update_menu()
            if notify:
                self.statusBar().showMessage("Прогресс сохранён в SQLite.",4000)
            return True
        except SaveError as error:
            self.statusBar().showMessage(str(error),10000)
            return False

    def set_ai_status(self, status):
        self.ai_status = status
        self.settings_screen.status.setText(status)
        self.menu.ai_status.setText(status)
        if self.workspace is not None:
            self.mode_label.setText(status)
            self.api_label.setText(status)

    def run_task(self, title, operation, completed):
        if self.is_busy():
            return
        self.root.setEnabled(False)
        self.activity.show()
        self.statusBar().showMessage(title)
        worker = Worker(operation,self)
        self._worker = worker
        self._task_callback = completed
        worker.completed.connect(self.task_completed)
        worker.failed.connect(lambda message:self.statusBar().showMessage(message,10000))
        def finished():
            self.root.setEnabled(True)
            self.activity.hide()
            if self.statusBar().currentMessage()==title:
                self.statusBar().showMessage("Готово.",3000)
            self._worker=None
            worker.deleteLater()
        worker.finished.connect(finished)
        worker.start()

    @Slot(object)
    def task_completed(self,result):
        try:
            self._task_callback(result)
        except (ValueError, SaveError) as error:
            self.statusBar().showMessage(str(error),8000)

    def send_dialogue(self,pid,question,tone='calm',topic_hint=None,evidence_id=None):
        request=self.engine.dialogue_request(pid,question,tone,topic_hint,evidence_id)
        provider=None if self.config.demo or not self.config.api_key else GeminiProvider(self.config.api_key,self.config.model,self.config.timeout_ms)
        agent=CharacterAgent(provider)
        def completed(reply):
            self.engine.commit_dialogue(request,reply)
            self.set_ai_status('GEMINI CONNECTED' if reply.source=='GEMINI' else 'AI DEMO MODE')
            self.refresh_state()
            if reply.notice:
                self.statusBar().showMessage(reply.notice+' Использован локальный ответ.',10000)
        if provider is None:
            completed(agent.reply(request))
        else:
            self.run_task('Собеседник обдумывает ответ…',lambda:agent.reply(request),completed)

    def apply_settings(self):
        settings=self.settings_screen
        self.config.api_key=settings.key.text().strip()
        self.config.model=settings.model.text().strip() or self.config.model
        self.config.demo=settings.demo.isChecked()
        self.config.scale=settings.scale.currentData()
        try:
            self.config.save(settings.remember.isChecked())
        except OSError:
            self.statusBar().showMessage('Настройки применены на эту сессию; записать их на диск не удалось.',7000)
        self.set_ai_status('AI DEMO MODE' if self.config.demo or not self.config.api_key else 'GEMINI: НЕ ПРОВЕРЕНО')
        self.statusBar().showMessage('Настройки применены. Масштаб изменится после перезапуска.',5000)

    def check_connection(self):
        # Проверка использует введённые значения и не сохраняет ключ без отдельного действия.
        key=self.settings_screen.key.text().strip()
        model=self.settings_screen.model.text().strip()
        if not key or not model:
            self.statusBar().showMessage('Укажите API-ключ и модель.',5000)
            return
        def operation():
            from ai.api_client import ProviderError
            try:
                return GeminiProvider(key,model).check()
            except ProviderError as error:
                return str(error)
        def completed(status):
            self.settings_screen.status.setText(status)
            if status=='GEMINI CONNECTED' and key==self.config.api_key and model==self.config.model and not self.config.demo:
                self.set_ai_status(status)
            elif status!='GEMINI CONNECTED' and not self.config.demo:
                self.set_ai_status('AI DEMO MODE')
            self.statusBar().showMessage(status,8000)
        self.run_task('Проверка Gemini…',operation,completed)
