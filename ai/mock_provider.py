import re
from ai.fact_validator import DialogueChoice


class MockAIProvider:
    """Локальный детерминированный маршрутизатор свободных вопросов."""
    name = "AI DEMO MODE"

    def choose(self, request: dict) -> dict:
        question = request['question'].lower().replace('ё', 'е')
        if re.search(r'камер|запис|охран|замет|видел|видела|провер|наблюд', question):
            topic = 'observations'
        elif re.search(r'зачем|почему|мотив|отношени|деньг|финанс|развод|ссор|работ|бизнес|документ', question):
            topic = 'motive'
        elif re.search(r'где|когда|алиби|врем|ушл|уход|верну|кабинет|вечер|ужин|наход|делал|делали', question):
            topic = 'alibi'
        else:
            topic = 'other'
        if request.get('topic_hint'):
            topic = request['topic_hint']
        reaction = 'nervous' if request['stress'] >= 70 else 'cooperative' if request['trust'] >= 50 else 'neutral'
        return {'topic': topic, 'reaction': reaction, 'order': list(range(len(request['candidates'][topic])))}
