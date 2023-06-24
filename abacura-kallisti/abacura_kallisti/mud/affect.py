from dataclasses import dataclass


@dataclass(slots=True)
class Affect:
    name: str
    hours: int
