from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Theme:
    id: Optional[int]
    title: str


@dataclass
class Answer:
    title: str
    is_correct: bool


@dataclass
class Question:
    id: int
    title: str
    theme_id: int
    answers: List[Answer]
