from typing import Any, ClassVar
from urllib.parse import urlparse
from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exako.apps.exercise.constants import ExerciseType, Language, Level
from exako.core.helper import normalize_array_text


def validate_audio_url(cls, audio_url: str) -> str:
    audio_extensions = ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']

    value_exception = ValueError('invalid audio_url.')
    try:
        result = urlparse(audio_url)
        if not all([result.scheme, result.netloc, result.path]):
            raise value_exception
    except ValueError:
        raise value_exception

    path = result.path.lower()
    if not any(path.endswith(ext) for ext in audio_extensions):
        raise value_exception
    return audio_url


def validate_image_url(cls, image_url: str) -> str:
    value_exception = ValueError('invalid image_url.')
    try:
        result = urlparse(image_url)
        if not all([result.scheme, result.netloc, result.path]):
            raise value_exception
    except ValueError:
        raise value_exception

    path = result.path.lower()
    if not path.endswith('.svg'):
        raise value_exception
    return image_url


def validate_distractors_reference(self):
    if self.term_reference in self.distractors:
        raise ValueError('term_reference cannot be in distractors.')
    if self.term_id in self.distractors:
        raise ValueError('term_id cannot be in distractors.')

    return self


class ExerciseCreateBase(BaseModel):
    term_id: UUID
    term_reference: UUID
    language: Language
    type: ExerciseType
    level: Level | None = None

    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def exercise_validate(cls, data):
        if cls is not ExerciseCreateBase or not isinstance(data, dict):
            return data

        exercise_type = (
            data.get('type')
            if isinstance(data.get('type'), ExerciseType)
            else ExerciseType(data.get('type'))
        )

        model = None
        for subclass in ExerciseCreateBase.__subclasses__():
            if subclass.exercise_type == exercise_type:
                model = subclass
                break

        if model is None:
            raise ValueError('exercise type is not valid.')

        return model(**data).model_dump()


class ExerciseCreateRead(BaseModel):
    id: PydanticObjectId
    term_id: UUID
    term_reference: UUID
    language: Language
    type: ExerciseType
    level: Level | None = None


class OrderSentenceCreate(ExerciseCreateBase):
    sentence: list[str]
    distractors: set[str] | None = None

    exercise_type: ClassVar[int] = ExerciseType.ORDER_SENTENCE

    @model_validator(mode='after')
    def validate_distractors(self):
        if self.distractors is None:
            return self

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


class ListenTermCreate(ExerciseCreateBase):
    audio_url: str
    answer: str

    exercise_type: ClassVar[int] = ExerciseType.LISTEN_TERM

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class ListenTermMChoiceCreate(ExerciseCreateBase):
    audio_url: str
    content: str
    distractors: dict[UUID, str] = Field(min_length=3)

    exercise_type: ClassVar[int] = ExerciseType.LISTEN_TERM_MCHOICE

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )


class ListenSentenceCreate(ExerciseCreateBase):
    audio_url: str
    answer: str

    exercise_type: ClassVar[int] = ExerciseType.LISTEN_SENTENCE

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class SpeakTermCreate(ExerciseCreateBase):
    audio_url: str
    phonetic: str
    content: str

    exercise_type: ClassVar[int] = ExerciseType.SPEAK_TERM

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class SpeakSentenceCreate(ExerciseCreateBase):
    audio_url: str
    phonetic: str
    content: str

    exercise_type: ClassVar[int] = ExerciseType.SPEAK_SENTENCE

    _validate_audio_url = field_validator('audio_url')(validate_audio_url)


class TermSentenceMChoiceCreate(ExerciseCreateBase):
    sentence: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=3)

    exercise_type: ClassVar[int] = ExerciseType.TERM_SENTENCE_MCHOICE

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )


class TermDefinitionMChoiceCreate(ExerciseCreateBase):
    content: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=3)

    exercise_type: ClassVar[int] = ExerciseType.TERM_DEFINITION_MCHOICE

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )


class TermImageMChoiceCreate(ExerciseCreateBase):
    image_url: str
    audio_url: str
    distractors: dict[UUID, str] = Field(min_length=3)

    exercise_type: ClassVar[int] = ExerciseType.TERM_IMAGE_MCHOICE

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_audio_url = field_validator('audio_url')(validate_audio_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )


class TermImageTextMChoiceCreate(ExerciseCreateBase):
    image_url: str
    answer: str
    distractors: dict[UUID, str] = Field(min_length=3)

    exercise_type: ClassVar[int] = ExerciseType.TERM_IMAGE_MCHOICE_TEXT

    _validate_image_url = field_validator('image_url')(validate_image_url)
    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )


class TermConnectionCreate(ExerciseCreateBase):
    content: str
    connections: dict[UUID, str] = Field(min_length=4)
    distractors: dict[UUID, str] = Field(min_length=8)

    exercise_type: ClassVar[int] = ExerciseType.TERM_CONNECTION

    _validate_distractors_reference = model_validator(mode='after')(
        validate_distractors_reference
    )

    @model_validator(mode='after')
    def validate_connections_reference(self):
        if self.term_reference in self.connections:
            raise ValueError('term_reference cannot be in connections.')
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


class ExerciseRead(BaseModel):
    type: ExerciseType
    url: str


class ExerciseResponse(BaseModel):
    correct: bool
    correct_answer: Any | None = None


class OrderSentenceRead(BaseModel):
    sentence: list[str] = Field(
        examples=[['almoçei', 'na', 'Ontem', 'casa', 'da', 'eu', 'mãe', 'minha.']]
    )


class ListenRead(BaseModel):
    audio_url: str = Field(examples=['https://example.com/my-audio.wav'])


class ListenMChoiceRead(BaseModel):
    choices: dict[str, str] = Field(
        examples=[
            {
                '1': 'https://example.com/my-audio.wav',
                '2': 'https://example.com/my-audio.wav',
                '3': 'https://example.com/my-audio.wav',
                '4': 'https://example.com/my-audio.wav',
            }
        ],
        description='Será retornado sempre 4 alternativas, incluindo a correta.',
    )
    content: str = Field(
        examples=['casa'],
        description='Conteúdo do termo a ser pronúnciado.',
    )


class SpeakRead(BaseModel):
    audio_url: str = Field(examples=['https://example.com/my-audio.wav'])
    phonetic: str = Field(examples=['/ˈhaʊ.zɪz/'])


class TermMChoiceRead(BaseModel):
    choices: dict[str, str] = Field(
        examples=[{'1': 'casa', '2': 'fogueira', '3': 'semana', '4': 'avião'}],
        description='Será retornado sempre 4 alternativas, incluindo a correta.',
    )
    content: str = Field(
        examples=['casa'],
        description='Conteúdo para preencher o header do exercício.',
    )


class ImageMChoiceRead(BaseModel):
    audio_url: str = Field(examples=['https://example.com/my-audio.wav'])
    choices: dict[str, str] = Field(
        examples=[
            {
                '1': 'https://example.com',
                '2': 'https://example.com',
                '3': 'https://example.com',
                '4': 'https://example.com',
            }
        ],
        description='Será retornado sempre 4 alternativas contendo o id do termo referido e o link para imagem do termo.',
    )


class TextImageMChoiceRead(BaseModel):
    image_url: str = Field(examples=['https://example.com/my-image.svg'])
    choices: dict[str, str] = Field(
        examples=[{'1': 'casa', '2': 'avião', '3': 'jaguar', '4': 'parede'}],
        description='Será retornado sempre 4 alternativas contendo o id do termo referido e o link para imagem do termo.',
    )


class TextConnectionRead(BaseModel):
    choices: dict[str, str] = Field(
        examples=[[{'1': 'casa', '2': 'avião', '3': 'jaguar', '4': 'parede'}]],
    )
    content: str = Field(
        examples=['casa'],
        description='Conteúdo relacionado as conexões.',
    )
