"""Детерминированные правила дела. Не зависит от Qt или сетевых сервисов."""
from dataclasses import dataclass, field
from datetime import datetime
import json

from core.case_manager import ROOT, load_case, load_characters
from core.character_state import CharacterState


def _read(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


@dataclass
class Message:
    speaker: str
    text: str
    source: str = ""
    time: str = field(default_factory=lambda: datetime.now().astimezone().strftime("%H:%M"))


@dataclass
class GameSession:
    started: bool = False
    section: str = "Обзор дела"
    suspect_id: str = "anna"
    notes: str = ""
    found: set[str] = field(default_factory=set)
    examined: set[str] = field(default_factory=set)
    asked: set[str] = field(default_factory=set)
    contradictions: set[str] = field(default_factory=set)
    characters: dict[str, CharacterState] = field(default_factory=dict)
    dialogues: dict[str, list[Message]] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)
    pinned: set[tuple[str, int]] = field(default_factory=set)
    result: dict | None = None
    ml_results: list[dict] = field(default_factory=list)
    accusation_draft: dict = field(default_factory=dict)

    def start_new(self) -> None:
        fresh = GameSession(started=True)
        self.__dict__.update(fresh.__dict__)


class GameEngine:
    def __init__(self, session: GameSession):
        self.session = session
        self.case = load_case()
        self.people = {p["id"]: p for p in load_characters()}
        self._profiles = _read("character_profiles.json")
        self._evidence = {e["id"]: e for e in _read("evidence.json")}
        self._scenario = _read("scenario_001.json")
        if not session.characters:
            session.characters = {pid: CharacterState(p["trust"], p["stress"]) for pid, p in self.people.items()}
            session.dialogues = {pid: [] for pid in self.people}

    def _active(self):
        if not self.session.started:
            raise ValueError("Сначала начните расследование.")
        if self.session.result is not None:
            raise ValueError("Дело завершено. Начните новое расследование для повторного прохождения.")

    def _person(self, pid: str):
        if pid not in self.people:
            raise ValueError("Неизвестный подозреваемый.")

    def _item(self, eid: str) -> dict:
        if eid not in self._evidence:
            raise ValueError("Неизвестная улика.")
        return self._evidence[eid]

    def _satisfies(self, requirements: dict) -> bool:
        sources = {"asked": self.session.asked, "examined": self.session.examined,
                   "secrets": {pid for pid, s in self.session.characters.items() if s.secret_revealed}}
        return all(set(ids) <= sources[key] for key, ids in requirements.items())

    def evidence_slots(self) -> list[dict]:
        """Возвращает только допустимые заголовки; запертые материалы анонимны."""
        slots = []
        for eid, e in self._evidence.items():
            available = self._satisfies(e["requires"])
            found = eid in self.session.found
            slots.append({"id": eid, "title": e["title"] if available or found else "Неизвестный материал",
                          "available": available, "found": found,
                          "examined": eid in self.session.examined})
        return slots

    def collect(self, eid: str):
        self._active()
        e = self._item(eid)
        if not self._satisfies(e["requires"]):
            raise ValueError("Оснований для получения этого материала пока нет.")
        if eid not in self.session.found:
            self.session.found.add(eid)
            self.session.journal.append(f"Получена улика: {e['title']}.")

    def examine(self, eid: str) -> dict:
        e = self._item(eid)
        if eid not in self.session.found:
            raise ValueError("Сначала получите материал.")
        if eid not in self.session.examined:
            self._active()
            self.session.examined.add(eid)
            self.session.journal.append(f"Изучено: {e['title']}. {e['description']}")
            for event in e["events"]:
                self.session.journal.append(f"Открыто событие {event['time']}: {event['title']}.")
        return self.evidence_detail(eid)

    def evidence_detail(self, eid: str) -> dict:
        e = self._item(eid)
        if eid not in self.session.examined:
            raise ValueError("Содержание доступно только после изучения.")
        return {key: e[key] for key in ("id", "title", "description", "source", "related", "icon")}

    def questions(self, pid: str) -> list[dict]:
        self._person(pid)
        return [{"id": q["id"], "text": q["text"]} for q in self._profiles[pid]["questions"]]

    def _record(self, pid: str, question: str, answer: str):
        self.session.dialogues[pid].extend([Message("detective", question), Message(pid, answer)])

    def ask(self, pid: str, topic: str, tone: str = "calm") -> str:
        self._active()
        self._person(pid)
        if tone not in ("calm", "pressure"):
            raise ValueError("Неизвестный тон допроса.")
        question = next((q for q in self._profiles[pid]["questions"] if q["id"] == topic), None)
        if question is None:
            raise ValueError("Неизвестная тема сценарного вопроса. Используйте свободный ввод в комнате допроса.")
        key = f"{pid}:{topic}"
        state = self.session.characters[pid]
        if key not in self.session.asked:
            state.react(tone)
        self.session.asked.add(key)
        # После признания персонаж не возвращается к уже опровергнутой лжи.
        answer = self._profiles[pid]["secret_response"] if state.secret_revealed else question["response"]
        if pid == "alexey" and topic == "alibi" and not state.secret_revealed:
            if "camera" in state.presented:
                answer = "Я уже признал визит в кабинет в 21:12. Сначала скрыл его, потому что боялся подозрений."
            elif "glass" in state.presented:
                answer = "Отпечатки на бокале мои. Это часть моих первоначальных показаний, которую я должен исправить."
        answer = state.voice + answer
        self._record(pid, question["text"], answer)
        self._update_contradictions()
        return answer

    def present(self, pid: str, eid: str, tone: str = "calm") -> str:
        self._active()
        self._person(pid)
        e = self._item(eid)
        if eid not in self.session.examined:
            raise ValueError("Предъявить можно только изученную улику.")
        if tone not in ("calm", "pressure"):
            raise ValueError("Неизвестный тон допроса.")
        baseline = "observations" if pid == "mikhail" else "alibi"
        if f"{pid}:{baseline}" not in self.session.asked:
            self.ask(pid, baseline, tone)
        state = self.session.characters[pid]
        if eid not in state.presented:
            state.react(tone, evidence=True)
        state.presented.add(eid)
        profile = self._profiles[pid]
        if set(profile["reveal_requires"]) <= state.presented:
            if not state.secret_revealed:
                state.secret_revealed = True
                self.session.journal.append(f"Уточнённые показания — {self.people[pid]['name']}: {profile['secret_response']}")
                if pid == "elena":
                    self.session.journal.append("Открыто событие 20:45: разговор Елены и Виктора о разводе.")
            response = profile["secret_response"]
        elif pid == "alexey" and eid in profile["reveal_requires"]:
            responses = {
                "camera": "Да, на записи я. Я заходил по деловому вопросу. Вы ещё не доказали, что бокал был отравлен.",
                "glass": "Отпечатки мои. Но одного бокала недостаточно, чтобы установить мотив. Проверьте документы.",
                "finance": "Это наши внутренние расчёты. Вы утверждаете, что это связано со смертью? Покажите остальные материалы.",
            }
            response = responses[eid]
        elif eid == "calls" and pid == "elena":
            response = "Сестра подтвердила разговор. Но звонок начался только в 21:08 — о более раннем времени он не говорит."
        else:
            response = "Я не могу объяснить эту улику. Проверьте её источник и поговорите с теми, кого она касается."
        answer = state.voice + response
        self._record(pid, f"Предъявлена улика: {e['title']}", answer)
        self._update_contradictions()
        return answer

    def _update_contradictions(self):
        for rule in self._scenario["contradictions"]:
            state = self.session.characters[rule["person"]]
            if (rule["id"] not in self.session.contradictions
                    and rule["statement"] in self.session.asked
                    and set(rule["evidence"]) <= state.presented
                    and (not rule["requires_secret"] or state.secret_revealed)):
                self.session.contradictions.add(rule["id"])
                self.session.journal.append("Подтверждённое противоречие: " + rule["text"])

    def pin(self, pid: str, index: int):
        self._person(pid)
        messages = self.session.dialogues[pid]
        if index < 0 or index >= len(messages) or messages[index].speaker == "detective":
            raise ValueError("Выберите показание подозреваемого.")
        if (pid, index) not in self.session.pinned:
            self.session.pinned.add((pid, index))
            self.session.journal.append(f"Показание — {self.people[pid]['name']}: {messages[index].text}")

    def timeline(self) -> list[dict]:
        events = list(self.case["timeline"])
        for eid, e in self._evidence.items():
            if eid in self.session.examined:
                events.extend(e["events"])
        if self.session.characters["elena"].secret_revealed:
            events.append({"time": "20:45", "title": "Разговор о разводе", "description": "Елена признала визит в кабинет."})
        return sorted(events, key=lambda e: e["time"][:5])

    def confirmed_facts(self) -> dict:
        """Структурированные сведения только из изученных материалов.

        Запись документа может требовать подтверждения — статус сохраняется.
        """
        ids = {fid for eid in self.session.examined for fid in self._evidence[eid]["confirms"]}
        return {fid: dict(self._scenario["facts"][fid]) for fid in sorted(ids)}

    def statistics(self) -> dict:
        s = self.session
        interviewed = sum(bool(messages) for messages in s.dialogues.values())
        # Полнота исследования не является оценкой вероятности вины.
        progress = round(100 * (len(s.examined) + interviewed + len(s.contradictions)) / 14)
        return {"found": len(s.found), "examined": len(s.examined), "interviewed": interviewed,
                "contradictions": len(s.contradictions), "progress": progress}

    def hints(self) -> str:
        s = self.session
        if not s.examined:
            return "Начните с запроса и изучения медицинского заключения в разделе «Улики»."
        if "mikhail:observations" not in s.asked:
            return "Спросите охранника, что он заметил и как проверить его слова."
        if "camera" not in s.examined:
            return "В разделе «Улики» можно запросить резерв регистратора. Изучите его."
        if not s.characters["anna"].secret_revealed:
            return "Обсудите алиби Анны и предъявите ей изученную запись."
        if "finance" not in s.examined:
            return "После уточнения показаний Анны проверьте материалы её стола в разделе «Улики»."
        if "alexey:alibi" not in s.asked:
            return "Уточните у Миронова его алиби."
        if "glass" not in s.examined:
            return "Запросите экспертизу предмета из кабинета в разделе «Улики»."
        if "alexey_visit" not in s.contradictions:
            return "Сопоставьте алиби Миронова с записью и предъявите ему материал."
        return "Проверьте остальных собеседников и сопоставьте медицинское заключение, запись, предмет и мотив. Решение — в разделе «Обвинение»."

    def accuse(self, pid: str, evidence_ids: list[str], explanation: str) -> dict:
        self._active()
        self._person(pid)
        selected = set(evidence_ids)
        if not selected <= self.session.examined:
            raise ValueError("В обвинении допустимы только изученные доказательства.")
        correct = pid == self._scenario["killer"]
        required = set(self._scenario["essential_evidence"])
        rules = set(self._scenario["essential_contradictions"])
        complete = correct and required <= selected and rules <= self.session.contradictions
        outcome = "Дело полностью раскрыто" if complete else "Преступник определён, но доказательств недостаточно" if correct else "Обвинён невиновный"
        score = (40 if correct else 0) + 10 * len(selected & required) + (20 if rules <= self.session.contradictions else 0)
        result = {"outcome": outcome, "score": score, "suspect": pid,
                  "selected": sorted(selected), "explanation": explanation.strip(),
                  "missing_evidence": sorted(required - selected),
                  "missing_evidence_titles": [self._evidence[eid]["title"] for eid in sorted(required - selected)],
                  "missing_contradictions": sorted(rules - self.session.contradictions),
                  "timeline": list(self._scenario["ending_timeline"]), "motive": self._scenario["motive"],
                  "roles": {self.people[p]['name']: v['real_motive'] for p, v in self._profiles.items()},
                  "found": [e['title'] for eid, e in self._evidence.items() if eid in self.session.found],
                  "missed": [e['title'] for eid, e in self._evidence.items() if eid not in self.session.found]}
        self.session.result = result
        self.session.journal.append("Итог: " + outcome)
        return result

    def dialogue_request(self, pid: str, question: str, tone: str = 'calm', topic_hint: str | None = None, evidence_id: str | None = None) -> dict:
        """Готовит снимок допустимых ответов без изменения реальной сессии."""
        from copy import deepcopy
        from ai.character_agent import CharacterAgent
        self._active()
        self._person(pid)
        if not question.strip() or len(question) > 2000:
            raise ValueError('Введите вопрос длиной от 1 до 2000 символов.')
        candidates = {}
        if evidence_id:
            clone = deepcopy(self)
            candidates['evidence'] = CharacterAgent.fragments(clone.present(pid, evidence_id, tone))
            topic_hint = 'evidence'
        else:
            for topic in ('alibi','motive','observations'):
                clone = deepcopy(self)
                candidates[topic] = CharacterAgent.fragments(clone.ask(pid, topic, tone))
            candidates['other'] = ['Я не уверен, что могу ответить на это. Спросите о моём алиби, отношениях с Виктором или о том, что я заметил.']
        state = self.session.characters[pid]
        person = self.people[pid]
        return {'pid':pid, 'question':question.strip(), 'tone':tone, 'topic_hint':topic_hint,
                'evidence_id':evidence_id, 'name':person['name'], 'role':person['role'],
                'personality':person['character'], 'trust':state.trust, 'stress':state.stress,
                'history':[{'speaker':m.speaker,'text':m.text} for m in self.session.dialogues[pid][-12:]],
                'candidates':candidates}

    def commit_dialogue(self, request: dict, reply):
        """Применяется только в потоке GUI после завершения запроса."""
        from ai.fact_validator import FactValidator
        self._active()
        pid = request['pid']
        self._person(pid)
        # Повторно проверяем выбор даже при замене AI-провайдера.
        choice = FactValidator().validate({'topic':reply.choice.topic,'reaction':reply.choice.reaction,'order':list(reply.choice.order)}, request['candidates'])
        if request.get('evidence_id'):
            self.present(pid, request['evidence_id'], request['tone'])
        elif choice.topic != 'other':
            self.ask(pid, choice.topic, request['tone'])
        else:
            self._record(pid, request['question'], '')
        messages = self.session.dialogues[pid]
        messages[-2].text = request['question']
        messages[-1].text = FactValidator().render(choice, request['candidates'])
        messages[-1].source = reply.source
