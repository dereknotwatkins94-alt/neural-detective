"""Содержит спойлеры. Проверки пути к разгадке и защиты игровых условий."""
import pytest
from core.game_engine import GameEngine, GameSession


@pytest.fixture
def game():
    session = GameSession()
    session.start_new()
    return GameEngine(session)


def study(game, eid):
    game.collect(eid)
    return game.examine(eid)


def essential_route(game):
    study(game, 'medical')
    game.ask('mikhail', 'observations')
    study(game, 'camera')
    game.present('anna', 'camera')
    study(game, 'finance')
    game.ask('alexey', 'alibi')
    study(game, 'glass')
    game.present('alexey', 'camera')


def test_initial_state_does_not_reveal_locked_content(game):
    slots = game.evidence_slots()
    assert [s['id'] for s in slots if s['available']] == ['medical']
    assert all(s['title'] == 'Неизвестный материал' for s in slots if not s['available'])
    assert len(game.timeline()) == 3
    assert not game.session.journal
    assert game.session.result is None
    with pytest.raises(ValueError):
        game.evidence_detail('camera')
    with pytest.raises(ValueError):
        game.collect('finance')
    assert not game.session.found


def test_cannot_present_unexamined_evidence(game):
    game.collect('medical')
    with pytest.raises(ValueError):
        game.present('alexey', 'medical')
    with pytest.raises(ValueError):
        game.examine('glass')
    assert not game.session.asked


def test_complete_solution_without_network_or_confession(game):
    essential_route(game)
    assert 'alexey_visit' in game.session.contradictions
    assert not game.session.characters['alexey'].secret_revealed
    result = game.accuse('alexey', ['medical','camera','glass','finance'], 'Мотив, способ, возможность и опровержение алиби.')
    assert result['outcome'] == 'Дело полностью раскрыто'
    assert result['score'] == 100
    assert len(result['timeline']) == 10
    assert len(result['roles']) == 4
    assert len(result['missed']) == 2


def test_all_six_clues_all_four_secrets_and_progress(game):
    essential_route(game)
    game.ask('elena','motive')
    study(game,'letters')
    game.present('elena','letters')
    study(game,'calls')  # Алиби автоматически зафиксировано до предъявления письма.
    game.present('mikhail','camera')
    for eid in ['camera','glass','finance']:
        game.present('alexey',eid)
    assert len(game.session.examined) == 6
    assert len(game.session.contradictions) == 4
    assert all(state.secret_revealed for state in game.session.characters.values())
    assert game.statistics()['progress'] == 100
    assert any(e['time'] == '20:45' for e in game.timeline())
    assert '20:45' in game.ask('elena','alibi')
    assert 'не возвращалась' not in game.ask('anna','alibi')
    assert 'В кабинет Орлова не заходил' not in game.ask('alexey','alibi')


def test_only_presented_material_changes_secret_state(game):
    essential_route(game)
    assert not game.session.characters['mikhail'].secret_revealed
    assert not game.session.characters['alexey'].secret_revealed
    game.present('elena','camera')
    assert not game.session.characters['elena'].secret_revealed
    assert not any(e['time']=='20:45' for e in game.timeline())


@pytest.mark.parametrize('pid,expected', [('alexey','Преступник определён, но доказательств недостаточно'), ('elena','Обвинён невиновный'), ('anna','Обвинён невиновный'), ('mikhail','Обвинён невиновный')])
def test_early_endings(game,pid,expected):
    result = game.accuse(pid, [], '')
    assert result['outcome'] == expected
    assert result['missed']
    assert result['motive']


@pytest.mark.parametrize('omitted',['medical','camera','glass','finance'])
def test_each_essential_evidence_required(game,omitted):
    essential_route(game)
    evidence = ['medical','camera','glass','finance']
    evidence.remove(omitted)
    result = game.accuse('alexey',evidence,'')
    assert result['outcome'] != 'Дело полностью раскрыто'
    assert result['score'] == 90
    assert result['missing_evidence'] == [omitted]


def test_evidence_alone_does_not_complete_interrogation(game):
    study(game,'medical')
    game.ask('mikhail','observations')
    study(game,'camera')
    game.present('anna','camera')
    study(game,'finance')
    game.ask('alexey','alibi')
    study(game,'glass')
    assert 'alexey_visit' not in game.session.contradictions
    result = game.accuse('alexey',['medical','camera','glass','finance'],'')
    assert result['score'] == 80
    assert result['missing_contradictions'] == ['alexey_visit']


def test_deduplication_pin_and_repeated_actions(game):
    study(game,'medical')
    study(game,'medical')
    assert len(game.session.journal) == 3
    game.ask('anna','alibi','pressure')
    before = (game.session.characters['anna'].stress, game.session.characters['anna'].trust)
    game.ask('anna','alibi','pressure')
    assert before == (game.session.characters['anna'].stress, game.session.characters['anna'].trust)
    game.pin('anna',1)
    game.pin('anna',1)
    assert len(game.session.pinned) == 1
    assert game.session.journal[-1].startswith('Показание')
    with pytest.raises(ValueError):
        game.pin('anna',0)
    with pytest.raises(ValueError):
        game.pin('anna',-1)


def test_stress_and_trust_change_tone_without_soft_lock(game):
    for topic in ('alibi','motive','observations'):
        response = game.ask('anna',topic,'pressure')
    assert response.startswith('[напряжённо]')
    game.ask('mikhail','observations')
    study(game,'camera')
    game.present('anna','camera','pressure')
    assert game.session.characters['anna'].secret_revealed
    assert all(0<=s.trust<=100 and 0<=s.stress<=100 for s in game.session.characters.values())


def test_finished_case_is_read_only(game):
    study(game,'medical')
    game.accuse('anna',[],'')
    assert game.examine('medical')['id'] == 'medical'
    for action in [lambda:game.ask('anna','alibi'), lambda:game.collect('medical'), lambda:game.present('anna','medical'), lambda:game.accuse('alexey',[],'')]:
        with pytest.raises(ValueError):
            action()


def test_invalid_input_does_not_mutate_game(game):
    for action in [lambda:game.ask('anna','кто убийца?'),lambda:game.ask('missing','alibi'),lambda:game.ask('anna','alibi','x'),lambda:game.collect('missing'),lambda:game.accuse('alexey',['finance'],'')]:
        with pytest.raises(ValueError):
            action()
    assert not game.session.asked
    assert not game.session.found
    assert game.session.result is None


def test_new_session_clears_all_progress(game):
    essential_route(game)
    game.session.notes='Моя версия'
    game.session.start_new()
    new_game=GameEngine(game.session)
    assert not new_game.session.examined
    assert not new_game.session.characters['anna'].secret_revealed
    assert not new_game.session.dialogues['anna']
    assert not new_game.session.notes


def test_camera_first_and_reverse_order_of_confrontations(game):
    game.ask('mikhail','observations')
    study(game,'camera')
    game.present('alexey','camera')  # Исходное алиби фиксируется автоматически.
    assert 'alexey_visit' in game.session.contradictions
    assert 'Я уже признал' in game.ask('alexey','alibi')
    game.present('anna','camera')
    study(game,'finance')
    game.present('alexey','finance')
    study(game,'medical')
    study(game,'glass')
    game.present('alexey','glass')
    assert game.session.characters['alexey'].secret_revealed
    assert game.accuse('alexey',['medical','camera','glass','finance'],'')['score']==100


def test_fact_visibility_and_scenario_references(game):
    assert game.confirmed_facts() == {}
    study(game,'medical')
    facts=game.confirmed_facts()
    assert set(facts)=={'poison','death_window'}
    assert facts['death_window']['value']==['21:25','21:45']
    # Неверная ссылка в сценарии должна быть замечена до запуска UI.
    import json
    from core.case_manager import ROOT
    scenario=json.loads((ROOT/'data/scenario_001.json').read_text(encoding='utf-8'))
    evidence=json.loads((ROOT/'data/evidence.json').read_text(encoding='utf-8'))
    assert all(fid in scenario['facts'] for e in evidence for fid in e['confirms'])
    assert scenario['facts']['death_window']['value'][0] <= scenario['truth']['death_time'] <= scenario['facts']['death_window']['value'][1]
    assert scenario['killer']==scenario['truth']['killer']
