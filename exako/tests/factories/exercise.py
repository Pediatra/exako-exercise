import json
from random import choice
from typing import ClassVar
from uuid import UUID, uuid4

from beanie import PydanticObjectId
from faker import Faker
from pydantic import BaseModel, Field

from exako.apps.computed import models as computed_models
from exako.apps.computed.models import ExerciseComputed
from exako.apps.exercise import models
from exako.core.constants import ExerciseType, Language, Level

faker = Faker()


def generate_alternatives(number):
    return {uuid4(): faker.word() for _ in range(number)}


class ExerciseBaseFactory(BaseModel):
    id: PydanticObjectId | None = None
    language: Language = Field(default_factory=lambda: choice(list(Language)))
    level: Level | None = None

    model: ClassVar = models.Exercise
    computed: ClassVar = computed_models.ExerciseComputed

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
    def generate_payload(cls, include=None, exclude=None, **kwargs):
        payload = cls(insert_mongo=False, **kwargs).model_dump_json(
            include=include,
            exclude=exclude,
            exclude_none=True,
        )
        json_dict = json.loads(payload)
        term_reference = json_dict.pop(cls.term_reference, None)
        if term_reference:
            json_dict['term_reference'] = term_reference
        return json.dumps(json_dict)

    @classmethod
    async def find_computed(cls, payload):
        json_dict = json.loads(payload)
        return await ExerciseComputed.find(
            {
                'type': ExerciseType(json_dict['type']),
                cls.term_reference: UUID(json_dict['term_reference']),
            },
            with_children=True,
        ).first_or_none()


class OrderSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.ORDER_SENTENCE
    sentence: list[str] = Field(default_factory=lambda: faker.sentence().split())
    distractors: list[str] | None = ['qawe', 'awr', 'q2awt', 'q245asr']
    term_example_id: UUID = Field(default_factory=uuid4)

    model: ClassVar = models.OrderSentence
    term_reference: ClassVar[str] = 'term_example_id'
    computed: ClassVar = computed_models.OrderSentenceComputed


class ListenTermFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_TERM
    audio_url: str = 'https://example.com/url.mp3'
    answer: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)

    model: ClassVar = models.ListenTerm
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.ListenTermComputed


class ListenTermMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_TERM_MCHOICE
    audio_url: str = 'https://example.com/url.mp3'
    content: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.ListenTermMChoice
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.ListenTermMChoiceComputed


class ListenSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.LISTEN_SENTENCE
    audio_url: str = 'https://example.com/url.mp3'
    answer: str = Field(default_factory=lambda: faker.word())
    term_example_id: UUID = Field(default_factory=uuid4)

    model: ClassVar = models.ListenSentence
    term_reference: ClassVar[str] = 'term_example_id'
    computed: ClassVar = computed_models.ListenSentenceComputed


class SpeakTermFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.SPEAK_TERM
    audio_url: str = 'https://example.com/url.mp3'
    phonetic: str = 'head'
    answer: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)

    model: ClassVar = models.SpeakTerm
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.SpeakTermComputed


class SpeakSentenceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.SPEAK_SENTENCE
    audio_url: str = 'https://example.com/url.mp3'
    phonetic: str = 'head'
    answer: str = Field(default_factory=lambda: faker.word())
    term_example_id: UUID = Field(default_factory=uuid4)

    model: ClassVar = models.SpeakSentence
    term_reference: ClassVar[str] = 'term_example_id'
    computed: ClassVar = computed_models.SpeakSentenceComputed


class TermSentenceMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_SENTENCE_MCHOICE
    sentence: str = Field(default_factory=lambda: faker.sentence())
    answer: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermSentenceMChoice
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.TermSentenceMChoiceComputed


class TermDefinitionMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_DEFINITION_MCHOICE
    content: str = Field(default_factory=lambda: faker.word())
    answer: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)
    term_definition_id: UUID = Field(default_factory=uuid4)
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermDefinitionMChoice
    term_reference: ClassVar[str] = 'term_definition_id'
    computed: ClassVar = computed_models.TermDefinitionMChoiceComputed


class TermImageMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_IMAGE_MCHOICE
    audio_url: str = 'https://example.com/url.mp3'
    image_url: str = 'https://example.com/url.svg'
    term_id: UUID = Field(default_factory=uuid4)
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermImageMChoice
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.TermImageMChoiceComputed


class TermImageTextMChoiceFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_IMAGE_TEXT_MCHOICE
    image_url: str = 'https://example.com/url.svg'
    answer: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )

    model: ClassVar = models.TermImageTextMChoice
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.TermImageTextMChoiceComputed


class TermConnectionFactory(ExerciseBaseFactory):
    type: ExerciseType = ExerciseType.TERM_CONNECTION
    content: str = Field(default_factory=lambda: faker.word())
    term_id: UUID = Field(default_factory=uuid4)
    connections: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(8)
    )
    distractors: dict[UUID, str] = Field(
        default_factory=lambda: generate_alternatives(16)
    )

    model: ClassVar = models.TermConnection
    term_reference: ClassVar[str] = 'term_id'
    computed: ClassVar = computed_models.TermConnectionComputed
