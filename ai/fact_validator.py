"""LLM выбирает разрешённые фрагменты, но не изменяет факты.

Свободный текст от провайдера никогда не выводится напрямую: это исключает
новые улики, посторонние секреты и подмену канона даже при prompt injection.
"""
from dataclasses import dataclass

REACTIONS = {
    "neutral": "", "guarded": "Я постараюсь ответить точнее. ",
    "nervous": "Мне трудно об этом говорить. ", "cooperative": "Хорошо, я объясню. ",
}
TOPICS = ("alibi", "motive", "observations", "other")


@dataclass(frozen=True)
class DialogueChoice:
    topic: str
    reaction: str = "neutral"
    order: tuple[int, ...] = ()


class FactValidator:
    def validate(self, payload: dict, candidates: dict[str, list[str]]) -> DialogueChoice:
        if not isinstance(payload, dict) or set(payload) != {"topic", "reaction", "order"}:
            raise ValueError("Некорректный формат ответа провайдера.")
        topic, reaction, order = payload['topic'], payload['reaction'], payload['order']
        if topic not in candidates or reaction not in REACTIONS or not isinstance(order, list):
            raise ValueError("Ответ выходит за рамки сценария.")
        # Полный набор фрагментов обязателен: нельзя удалить существенный факт.
        if any(type(i) is not int for i in order) or sorted(order) != list(range(len(candidates[topic]))):
            raise ValueError("Недопустимый набор фактов.")
        return DialogueChoice(topic, reaction, tuple(order))

    def render(self, choice: DialogueChoice, candidates: dict[str, list[str]]) -> str:
        return REACTIONS[choice.reaction] + ' '.join(candidates[choice.topic][index] for index in choice.order)
