from random import random
from typing import Annotated
from uuid import UUID

from beanie import Document, Indexed
from fastapi_pagination import Params
from fief_client import FiefUserInfo
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from exako.core.constants import ExerciseType, Language, Level
from exako.core.helper import fetch_card_terms


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
    distractors: dict[UUID, str]
    term_id: Annotated[UUID, Indexed()]

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
    answer: str
    term_id: Annotated[UUID, Indexed()]

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
    answer: str
    term_example_id: Annotated[UUID, Indexed()]

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
    distractors: dict[UUID, str]
    term_id: Annotated[UUID, Indexed()]

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
    distractors: dict[UUID, str]
    term_id: Annotated[UUID, Indexed()]
    term_definition_id: Annotated[UUID, Indexed()]

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
    distractors: dict[UUID, str]
    term_id: Annotated[UUID, Indexed()]

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
    distractors: dict[UUID, str]

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
    connections: dict[UUID, str]
    distractors: dict[UUID, str]

    class Settings:
        indexes = [
            IndexModel(
                [('term_id', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_connection_unique_index',
                partialFilterExpression={'type': ExerciseType.TERM_CONNECTION},
            ),
        ]
