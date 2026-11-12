from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QMessageBox


def ask(window,pid,topic):
    window.select_suspect(pid)
    room=window.interrogation
    room.question.setCurrentIndex(room.question.findData(topic))
    room.ask_button.click()


def study(window,eid):
    window.navigate('Улики')
    action=window.evidence_screen.slots[eid][2]
    action.click()  # Получить.
    action.click()  # Изучить.


def present(window,pid,eid):
    window.prepare_evidence(pid,eid)
    window.interrogation.present_button.click()


def test_complete_game_through_ui(window,monkeypatch,app):
    window.start_new()
    study(window,'medical')
    ask(window,'mikhail','observations')
    study(window,'camera')
    present(window,'anna','camera')
    assert '21:17' in window.interrogation.history.toPlainText()
    window.interrogation.pin_message(QUrl('pin:3'))
    assert window.session.pinned
    study(window,'finance')
    ask(window,'alexey','alibi')
    study(window,'glass')
    present(window,'alexey','camera')
    assert window.evidence_count.text() == 'Улики: 4 / 6'
    assert 'Подтверждённое противоречие' in window.journal.events.toPlainText()
    assert '21:12' in window.overview.timeline_label.text()
    window.navigate('Обвинение')
    form=window.accusation
    form.suspect.setCurrentIndex(form.suspect.findData('alexey'))
    for eid in ['medical','camera','glass','finance']:
        form.checks[eid].setChecked(True)
    form.explanation.setPlainText('<b>Моя версия: проверить документы</b>')
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.StandardButton.Cancel)
    form.submit()
    assert window.session.result is None
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.StandardButton.Yes)
    form.submit()
    app.processEvents()
    assert window.session.result['score'] == 100
    assert form.result_panel.isVisible()
    assert not form.form.isVisible()
    assert '<b>Моя версия' in form.result_text.text()
    assert not window.interrogation.ask_button.isEnabled()
    assert not window.interrogation.present_button.isEnabled()


def test_locked_titles_and_ending_are_not_rendered(window):
    window.start_new()
    assert all(w[0].text()=='Неизвестный материал' for eid,w in window.evidence_screen.slots.items() if eid!='medical')
    assert not window.accusation.result_text.text()
    assert not window.accusation.result_panel.isVisible()
    assert not window.accusation.checks['finance'].isEnabled()


def test_progress_survives_menu_but_resets_on_new_game(window,monkeypatch):
    window.start_new()
    study(window,'medical')
    ask(window,'anna','alibi')
    window.show_menu()
    window.resume()
    assert window.session.examined=={'medical'}
    assert window.interrogation.history.toPlainText()
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.StandardButton.Yes)
    window.start_new()
    assert not window.session.examined
    assert not window.interrogation.history.toPlainText().startswith('Детектив')
    assert all(not state.secret_revealed for state in window.session.characters.values())


def test_dynamic_cards_keep_controls_inside_at_1366x768(window,app):
    window.start_new()
    window.resize(1366,768)
    study(window,'medical')
    ask(window,'mikhail','observations')
    study(window,'camera')
    window.evidence_screen.open('camera')
    app.processEvents()
    for title,status,action in window.evidence_screen.slots.values():
        assert action.height()>=42
        assert action.geometry().bottom()<action.parentWidget().height()
    assert window.evidence_screen.links.count()==3
    for i in range(3):
        action=window.evidence_screen.links.itemAt(i).widget()
        assert action.geometry().bottom()<action.parentWidget().height()
    window.navigate('Журнал расследования')
    app.processEvents()
    assert window.journal.editor.height()==200
    scroll=window.pages.currentWidget()
    assert scroll.verticalScrollBar().maximum()>0
