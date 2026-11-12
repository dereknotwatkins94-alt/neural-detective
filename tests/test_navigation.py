import pytest
from PySide6.QtWidgets import QMessageBox
from ui.main_window import SECTIONS
from core.case_manager import load_case, load_characters


def test_menu_and_secondary_pages(window):
    assert window.root.currentWidget() is window.menu
    assert not window.menu.resume_button.isEnabled()
    window.menu.archive_button.click()
    assert window.root.currentWidget() is window.archive
    window.show_menu()
    window.menu.settings_button.click()
    assert window.root.currentWidget() is window.settings


@pytest.mark.parametrize("section", [item[0] for item in SECTIONS])
def test_navigation_buttons(window, section, app):
    window.menu.new_button.click()
    window.nav_buttons[section].click()
    app.processEvents()
    assert window.session.section == section
    assert window.nav_buttons[section].isChecked()
    assert window.pages.currentIndex() == [item[0] for item in SECTIONS].index(section)


def test_resume_keeps_notes_and_section(window):
    window.start_new()
    window.journal.editor.setPlainText("Проверить время обнаружения тела")
    window.navigate("Журнал расследования")
    window.show_menu()
    window.menu.resume_button.click()
    assert window.root.currentWidget() is window.workspace
    assert window.session.section == "Журнал расследования"
    assert "обнаружения" in window.journal.editor.toPlainText()


def test_profiles_select_interrogation(window):
    window.start_new()
    screen = window.pages.widget(1).widget().layout().itemAt(0).widget()
    for btn, p in zip(screen.profile_buttons, window.characters):
        btn.click()
        assert window.session.section == "Допрос"
        assert window.session.suspect_id == p["id"]
        assert window.interrogation.name.text() == p["name"]


def test_new_session_confirm_and_cancel(window, monkeypatch):
    window.start_new()
    window.session.notes = "Сохранить до подтверждения"
    old_workspace = window.workspace
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    window.start_new()
    assert window.workspace is old_workspace
    assert window.session.notes
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.start_new()
    assert window.session.notes == ""
    assert window.workspace is not old_workspace
    assert window.session.section == "Обзор дела"


def test_close_saves_notes(window, monkeypatch):
    window.start_new()
    window.journal.editor.setPlainText("Наблюдение")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    assert window.close()
    assert window.save_manager.load().notes == "Наблюдение"


def test_new_window_does_not_pretend_to_load_save(window):
    assert not window.session.started
    assert window.session.notes == ""


def test_public_data_and_ids():
    assert load_case()["id"] == "001"
    characters = load_characters()
    assert len({p["id"] for p in characters}) == 4
    assert all("secrets" not in p and "killer" not in p for p in characters)
