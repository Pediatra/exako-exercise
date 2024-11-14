from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from exako.core.constants import ExerciseType


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


def validate_distractors_reference(field):
    def wrapper(self):
        reference_field = getattr(self, field)
        if reference_field in self.distractors:
            raise ValueError(f'{field} cannot be in distractors.')
        return self

    return wrapper


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
        description='Conteúdo que ficará no header.',
    )


class SpeakRead(BaseModel):
    audio_url: str = Field(examples=['https://example.com/my-audio.wav'])
    phonetic: str = Field(examples=['/ˈhaʊ.zɪz/'])
    content: str = Field(
        examples=['casa'],
        description='Conteúdo que ficará no header.',
    )


class TermMChoiceRead(BaseModel):
    choices: dict[str, str] = Field(
        examples=[{'1': 'casa', '2': 'fogueira', '3': 'semana', '4': 'avião'}],
        description='Será retornado sempre 4 alternativas, incluindo a correta.',
    )
    content: str = Field(
        examples=['casa'],
        description='Conteúdo que ficará no header.',
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
