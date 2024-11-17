from datetime import date
from typing import Any

from pydantic import BaseModel, model_validator

from exako.core.constants import ExerciseType, Language, Level


class HistoryInfo(BaseModel):
    correct: int
    incorret: int
    streak: int


class HistoryRead(BaseModel):
    type: ExerciseType
    correct: bool
    response: dict[str, Any]
    request: dict[str, Any]


class HistoryStatistic(BaseModel):
    correct: int
    incorrect: int


class HistoryStatisticQuery(BaseModel):
    start_date: date
    end_date: date
    type: ExerciseType | None = None
    level: Level | None = None
    language: Language | None = None

    @model_validator(mode='after')
    def check_date_order(self):
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date.')
        return self
