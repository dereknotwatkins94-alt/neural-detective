from dataclasses import dataclass, field


@dataclass
class CharacterState:
    trust: int
    stress: int
    secret_revealed: bool = False
    presented: set[str] = field(default_factory=set)

    def react(self, tone: str, evidence: bool = False) -> None:
        self.trust = max(0, min(100, self.trust + (5 if tone == "calm" else -8)))
        self.stress = max(0, min(100, self.stress + (12 if evidence else -3 if tone == "calm" else 10)))

    @property
    def voice(self) -> str:
        if self.stress >= 70:
            return "[напряжённо] "
        if self.trust >= 50:
            return "[откровеннее] "
        return "[сдержанно] "
