from dataclasses import dataclass
import re
from ai.api_client import AIProvider, ProviderError
from ai.fact_validator import FactValidator, DialogueChoice
from ai.mock_provider import MockAIProvider


@dataclass(frozen=True)
class AgentReply:
    choice: DialogueChoice
    text: str
    source: str
    notice: str = ''


class CharacterAgent:
    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or MockAIProvider()
        self.validator = FactValidator()

    @staticmethod
    def fragments(text: str) -> list[str]:
        # Внутренние десятичные числа/время не режем, только конец предложения.
        return [part.strip() for part in re.split(r'(?<=[.!?])\s+', text) if part.strip()]

    def reply(self, request: dict) -> AgentReply:
        notice = ''
        for _ in range(2):
            try:
                payload = self.provider.choose(request)
                choice = self.validator.validate(payload, request['candidates'])
                hint = request.get('topic_hint')
                if hint and choice.topic != hint:
                    raise ValueError('Тема не соответствует действию.')
                return AgentReply(choice, self.validator.render(choice, request['candidates']), self.provider.name)
            except ProviderError as error:
                notice = str(error)
                break
            except (ValueError, TypeError, KeyError):
                notice = 'Ответ провайдера отклонён проверкой фактов.'
        fallback = MockAIProvider().choose(request)
        if request.get('topic_hint') == 'evidence':
            fallback = {'topic':'evidence','reaction':'neutral','order':list(range(len(request['candidates']['evidence'])))}
        choice = self.validator.validate(fallback, request['candidates'])
        return AgentReply(choice, self.validator.render(choice, request['candidates']), 'AI DEMO MODE', notice)
