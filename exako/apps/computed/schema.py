from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exako.apps.exercise.schema import (
    validate_audio_url,
    validate_distractors_reference,
    validate_image_url,
)
from exako.core.constants import ExerciseType, Language
from exako.core.helper import normalize_array_text


class ExerciseCreateBase(BaseModel):
    type: ExerciseType
    term_reference: UUID

    model_config = ConfigDict(extra='allow')


class ExerciseCreateRead(BaseModel):
    id: PydanticObjectId
    type: ExerciseType
    language: Language


class OrderSentenceSchema(BaseModel):
    sentence: list[str]
    distractors: list[str]
    term_example_id: UUID

    @model_validator(mode='after')
    def validate_distractors(self):
        normalized_sentence = normalize_array_text(self.sentence)
        normalized_distractors = normalize_array_text(self.distractors)

        intersection = set(normalized_sentence).intersection(
            set(normalized_distractors)
        )

        if len(intersection) > 0:
            raise ValueError(
                'an intersection was found between sentence list and distractors.'
            )

        return self


class ListenTermSchema(BaseModel):
    audio_url: str
    answer: str
    term_id: UUID

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class ListenTermMChoiceSchema(BaseModel):
    audio_url: str
    content: str
    distractors: dict[UUID, str] = Field(min_length=6)
    term_id: UUID

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )


class ListenSentenceSchema(BaseModel):
    audio_url: str
    answer: str
    term_example_id: UUID

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class SpeakTermSchema(BaseModel):
    audio_url: str
    phonetic: str
    answer: str
    term_id: UUID

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class SpeakSentenceSchema(BaseModel):
    audio_url: str
    phonetic: str
    answer: str
    term_example_id: UUID

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class TermSentenceMChoiceSchema(BaseModel):
    sentence: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=6)
    term_id: UUID

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )


class TermDefinitionMChoiceSchema(BaseModel):
    content: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=6)
    term_id: UUID
    term_definition_id: UUID

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_definition_id')
    )


class TermImageMChoiceSchema(BaseModel):
    image_url: str
    audio_url: str
    term_id: UUID
    distractors: dict[UUID, str] = Field(min_length=6)

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )


class TermImageTextMChoiceSchema(BaseModel):
    image_url: str
    answer: str
    term_id: UUID
    distractors: dict[UUID, str] = Field(min_length=6)

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )


class TermConnectionSchema(BaseModel):
    content: str
    term_id: UUID
    connections: dict[UUID, str] = Field(min_length=8)
    distractors: dict[UUID, str] = Field(min_length=16)

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )

    @model_validator(mode='after')
    def validate_connections_reference(self):
        if self.term_id in self.connections:
            raise ValueError('term_id cannot be in connections.')
        return self

    @model_validator(mode='after')
    def validate_intersections(self):
        distractors = set(self.distractors.keys())
        connections = set(self.connections.keys())

        if len(distractors.intersection(connections)) > 0:
            raise ValueError(
                'an intersection was found between distractors and connections.'
            )

        return self
