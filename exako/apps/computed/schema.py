from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from exako.core.constants import ExerciseType, Language


class ExerciseCreateBase(BaseModel):
    type: ExerciseType
    term_reference: UUID

    model_config = ConfigDict(extra='allow')


class ExerciseCreateRead(BaseModel):
    id: PydanticObjectId
    type: ExerciseType
    language: Language
