from random import random
from typing import Annotated
from uuid import UUID

from beanie import Document, Indexed
from fastapi_pagination import Params
from fief_client import FiefUserInfo
from pydantic import Field, field_validator, model_validator
from pymongo import ASCENDING, IndexModel

from exako.apps.exercise.schema import (
    validate_audio_url,
    validate_distractors_reference,
    validate_image_url,
)
from exako.core.constants import ExerciseType, Language, Level
from exako.core.helper import fetch_card_terms, normalize_array_text


class Exercise(Document):
    language: Annotated[Language, Indexed()]
    type: Annotated[ExerciseType, Indexed()]
    level: Level | None = None
    random_score: float = Field(default_factory=random)

    async def list(
        self,
        languages: list[Language],
        types: list[ExerciseType],
        levels: list[Level],
        cardsets: list[int],
        seed: float,
        user: FiefUserInfo,
        params: Params,
    ):
        main_pipeline = [
            {'$match': {'language': {'$in': languages}}},
            {'$addFields': {'order_no': {'$mod': ['$random_score', seed]}}},
        ]

        if ExerciseType.RANDOM not in types:
            main_pipeline.append({'$match': {'type': {'$in': types}}})

        if levels:
            main_pipeline.append({'$match': {'level': {'$in': levels}}})

        if cardsets:
            term_ids = await fetch_card_terms(user, cardsets, params)
            if term_ids:
                union_pipeline = [
                    {'$match': {'term_id': {'$in': term_ids}}},
                    {'$addFields': {'order_no': -1}},
                ]
                main_pipeline += [
                    {'$unionWith': {'coll': 'exercise', 'pipeline': union_pipeline}}
                ]

        main_pipeline += [
            {'$sort': {'order_no': ASCENDING}},
            {'$unset': 'order_no'},
        ]

        return Exercise.aggregate(main_pipeline)

    class Settings:
        is_root = True
        name = 'exercises'


class OrderSentence(Exercise):
    sentence: list[str]
    distractors: list[str]
    term_example_id: Annotated[UUID, Indexed()]

    @model_validator(mode='after')
    def validate_distractors(self):
        normalized_sentence = normalize_array_text(self.sentence)
        normalized_distractors = normalize_array_text(self.distractors)

        intersection = set(normalized_sentence).intersection(
            set(normalized_distractors)
        )

        if len(intersection) > 0:
            self.distractors = {
                item
                for item, norm_item in zip(self.distractors, normalized_distractors)
                if norm_item not in intersection
            }

        return self

    class Settings:
        indexes = [
            IndexModel(
                [('term_example_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='order_sentence_unique_index',
                partialFilterExpression={'type': ExerciseType.ORDER_SENTENCE},
            ),
        ]


class ListenTerm(Exercise):
    audio_url: str
    answer: str
    term_id: Annotated[UUID, Indexed()]

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='listen_term_unique_index',
                partialFilterExpression={'type': ExerciseType.LISTEN_TERM},
            ),
        ]


class ListenTermMChoice(Exercise):
    audio_url: str
    content: str
    term_id: Annotated[UUID, Indexed()]
    distractors: dict[UUID, str] = Field(min_length=6)

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='listen_term_mchoice_unique_index',
                partialFilterExpression={'type': ExerciseType.LISTEN_TERM_MCHOICE},
            ),
        ]


class ListenSentence(Exercise):
    audio_url: str
    answer: str
    term_example_id: Annotated[UUID, Indexed()]

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)

    class Settings:
        indexes = [
            IndexModel(
                [('term_example_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='listen_sentence_unique_index',
                partialFilterExpression={'type': ExerciseType.LISTEN_SENTENCE},
            ),
        ]


class SpeakTerm(Exercise):
    audio_url: str
    phonetic: str
    content: str
    term_id: Annotated[UUID, Indexed()]

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='speak_term_unique_index',
                partialFilterExpression={'type': ExerciseType.SPEAK_TERM},
            ),
        ]


class SpeakSentence(Exercise):
    audio_url: str
    phonetic: str
    content: str
    term_example_id: Annotated[UUID, Indexed()]

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)

    class Settings:
        indexes = [
            IndexModel(
                [('term_example_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='speak_sentence_unique_index',
                partialFilterExpression={'type': ExerciseType.SPEAK_SENTENCE},
            ),
        ]


class TermSentenceMChoice(Exercise):
    sentence: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=6)
    term_id: Annotated[UUID, Indexed()]

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_sentence_mchoice_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_SENTENCE_MCHOICE},
            ),
        ]


class TermDefinitionMChoice(Exercise):
    content: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=6)
    term_id: Annotated[UUID, Indexed()]
    term_definition_id: Annotated[UUID, Indexed()]

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_definition_id')
    )

    class Settings:
        indexes = [
            IndexModel(
                [
                    ('term_definition_id', ASCENDING),
                    ('term_id', ASCENDING),
                    ('type', ASCENDING),
                ],
                unique=True,
                name='term_definition_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_DEFINITION_MCHOICE},
            ),
        ]


class TermImageMChoice(Exercise):
    image_url: str
    audio_url: str
    term_id: Annotated[UUID, Indexed()]
    distractors: dict[UUID, str] = Field(min_length=6)

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_image_mchoice_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_IMAGE_MCHOICE},
            ),
        ]


class TermImageTextMChoice(Exercise):
    image_url: str
    answer: str
    term_id: Annotated[UUID, Indexed()]
    distractors: dict[UUID, str] = Field(min_length=6)

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference('term_id')
    )

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_image_text_mchoice_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_IMAGE_TEXT_MCHOICE},
            ),
        ]


class TermConnection(Exercise):
    content: str
    term_id: Annotated[UUID, Indexed()]
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

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_connection_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_CONNECTION},
            ),
        ]
