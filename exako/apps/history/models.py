from datetime import datetime
from typing import Any
from uuid import UUID

from beanie import Document, Link
from pydantic import Field

from exako.apps.exercise.models import Exercise


class ExerciseHistory(Document):
    exercise: Link[Exercise]
    user_id: UUID
    correct: bool
    created_at: datetime = Field(default_factory=datetime.now)
    response: dict[str, Any]
    request: dict[str, Any]

    class Settings:
        name = 'exercise_history'
