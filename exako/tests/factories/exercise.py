from random import choice
from typing import ClassVar
from uuid import UUID, uuid4

from beanie import PydanticObjectId
from faker import Faker
from pydantic import BaseModel, Field

from exako.apps.exercise import models
from exako.apps.exercise.constants import ExerciseType, Language, Level

faker = Faker()


def generate_alternatives(number):
    return {uuid4(): faker.word() for _ in range(number)}


class ExerciseBaseFactory(BaseModel):
    id: PydanticObjectId | None = None
    term_id: UUID = Field(default_factory=uuid4)
    term_reference: UUID = Field(default_factory=uuid4)
    language: Language = Field(default_factory=lambda: choice(list(Language)))
    level: Level | None = None

    model: ClassVar = models.Exercise

    def __new__(cls, *, insert_mongo=True, **data):
        instance = super().__new__(cls)
        if not insert_mongo:
            return instance
        cls.__init__(instance, **data)
        return cls.model(**instance.model_dump(exclude_none=True)).insert()

    @classmethod
    async def insert_batch(cls, *, size, **kwargs):
        return [await cls(**kwargs) for _ in range(size)]

    @classmethod
    def generate_payload(cls, **kwargs):
        return cls(insert_mongo=False, **kwargs).model_dump_json(exclude_none=True)


class OrderSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.ORDER_SENTENCE
    sentence: list[str] = Field(default_factory=lambda: faker.sentence().split())
    distractors: list[str] | None = ['qawe', 'awr', 'q2awt', 'q245asr']

    model: ClassVar = models.OrderSentence


class ListenTermFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_TERM
    audio_url: str = 'https://example.com/url.mp3'
    answer: str = Field(default_factory=lambda: faker.word())

    model: ClassVar = models.ListenTerm


class ListenTermMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_TERM_MCHOICE
    audio_url: str = 'https://example.com/url.mp3'
    content: str = Field(default_factory=lambda: faker.word())
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.ListenTermMChoice


class ListenSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_SENTENCE
    audio_url: str = 'https://example.com/url.mp3'
    answer: str = Field(default_factory=lambda: faker.word())

    model: ClassVar = models.ListenSentence


class SpeakTermFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.SPEAK_TERM
    audio_url: str = 'https://example.com/url.mp3'
    phonetic: str = 'head'
    content: str = Field(default_factory=lambda: faker.word())

    model: ClassVar = models.SpeakTerm


class SpeakSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.SPEAK_SENTENCE
    audio_url: str = 'https://example.com/url.mp3'
    phonetic: str = 'head'
    content: str = Field(default_factory=lambda: faker.word())

    model: ClassVar = models.SpeakSentence


class TermSentenceMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_SENTENCE_MCHOICE
    sentence: str = Field(default_factory=lambda: faker.sentence())
    answer: str = Field(default_factory=lambda: faker.word())
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermSentenceMChoice


class TermDefinitionMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_DEFINITION_MCHOICE
    content: str = Field(default_factory=lambda: faker.word())
    answer: str = Field(default_factory=lambda: faker.word())
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermDefinitionMChoice


class TermImageMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_IMAGE_MCHOICE
    audio_url: str = 'https://example.com/url.mp3'
    image_url: str = 'https://example.com/url.svg'
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermImageMChoice


class TermImageTextMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_IMAGE_MCHOICE_TEXT
    image_url: str = 'https://example.com/url.svg'
    answer: str = Field(default_factory=lambda: faker.word())
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermImageTextMChoice


class TermConnectionFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_CONNECTION
    content: str = Field(default_factory=lambda: faker.word())
    connections: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(16)
    )

    model: ClassVar = models.TermConnection
