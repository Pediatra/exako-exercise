from random import random
from typing import Annotated
from uuid import UUID

from beanie import Document, Indexed
from fastapi_pagination import Params
from fief_client import FiefUserInfo
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from exako.apps.exercise.constants import ExerciseType, Language, Level
from exako.core.helper import fetch_card_terms


class Exercise(Document):
    term_id: Annotated[UUID, Indexed()]
    term_reference: UUID
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
        indexes = [
            IndexModel(
                [('term_reference', ASCENDING), ('type', ASCENDING)],
                unique=True,
                name='term_type_unique_index',
            ),
        ]


class OrderSentence(Exercise):
    sentence: list[str]
    distractors: list[str] | None = None


class ListenTerm(Exercise):
    audio_url: str
    answer: str


class ListenTermMChoice(Exercise):
    audio_url: str
    content: str
    distractors: dict[UUID, str]


class ListenSentence(Exercise):
    audio_url: str
    answer: str


class SpeakTerm(Exercise):
    audio_url: str
    phonetic: str
    content: str


class SpeakSentence(Exercise):
    audio_url: str
    phonetic: str
    content: str


class TermSentenceMChoice(Exercise):
    sentence: str
    answer: str
    distractors: dict[UUID, str]


class TermDefinitionMChoice(Exercise):
    content: str
    answer: str
    distractors: dict[UUID, str]


class TermImageMChoice(Exercise):
    image_url: str
    audio_url: str
    distractors: dict[UUID, str]


class TermImageTextMChoice(Exercise):
    image_url: str
    answer: str
    distractors: dict[UUID, str]


class TermConnection(Exercise):
    content: str
    connections: dict[UUID, str]
    distractors: dict[UUID, str]


exercise_map: dict[ExerciseType, type[Exercise]] = {
    ExerciseType.ORDER_SENTENCE: OrderSentence,
    ExerciseType.LISTEN_TERM: ListenTerm,
    ExerciseType.LISTEN_SENTENCE: ListenSentence,
    ExerciseType.LISTEN_TERM_MCHOICE: ListenTermMChoice,
    ExerciseType.SPEAK_TERM: SpeakTerm,
    ExerciseType.SPEAK_SENTENCE: SpeakSentence,
    ExerciseType.TERM_SENTENCE_MCHOICE: TermSentenceMChoice,
    ExerciseType.TERM_DEFINITION_MCHOICE: TermDefinitionMChoice,
    ExerciseType.TERM_IMAGE_MCHOICE: TermImageMChoice,
    ExerciseType.TERM_IMAGE_MCHOICE_TEXT: TermImageTextMChoice,
    ExerciseType.TERM_CONNECTION: TermConnection,
}
