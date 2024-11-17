import inspect
from abc import ABC, abstractmethod
from random import randint, sample, shuffle
from typing import Annotated, Any, Callable
from uuid import UUID

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fief_client import FiefUserInfo
from pydantic import BaseModel, Field, create_model

from exako.apps.exercise import models
from exako.apps.exercise.voice import text
from exako.apps.exercise.voice.transcriber import trascribe_to_text
from exako.apps.history.models import ExerciseHistory
from exako.auth import current_user
from exako.core import helper
from exako.core import schema as core_schema
from exako.core.constants import ExerciseType


class ExerciseBase(ABC):
    exercise_type: ExerciseType

    async def __init__(
        self,
        exercise_id: PydanticObjectId,
    ):
        instance = await models.Exercise.find(
            {
                'id': exercise_id,
                'type': self.exercise_type,
            },
            with_children=True,
        ).first_or_none()
        if instance is None:
            raise HTTPException(status_code=404, detail='exercise not found.')
        self.instance = instance

    @abstractmethod
    def build(self) -> dict: ...

    @property
    @abstractmethod
    def correct_answer(self) -> Any: ...

    @abstractmethod
    def assert_answer(self, answer: dict) -> bool: ...

    async def check(
        self,
        user_id: str,
        answer: dict,
        exercise_request: dict,
    ) -> dict:
        correct = self.assert_answer(answer)
        check_response = {
            'correct': correct,
            'correct_answer': self.correct_answer,
        }
        await ExerciseHistory(
            exercise=self.instance,
            user_id=user_id,
            correct=correct,
            response={**answer, **check_response},
            request=exercise_request,
        ).insert()
        return check_response

    # fastapi endpoint methods

    @classmethod
    def generate_build_endpoint(
        cls, exercise_schema: type[BaseModel]
    ) -> tuple[Callable, dict]:
        async def build_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[ExerciseBase, Depends(cls)],
        ):
            return exercise_schema(**exercise_builder.build())

        path_options = {
            'responses': {
                **core_schema.NOT_AUTHENTICATED,
                **core_schema.OBJECT_NOT_FOUND,
            },
        }
        return build_endpoint, path_options

    @classmethod
    def generate_exercise_response(cls):
        correct_answer_signarute = inspect.signature(cls.correct_answer.fget)
        correct_answer_type = correct_answer_signarute.return_annotation
        return create_model(
            f'ExerciseResponse{cls.__name__}',
            correct=(bool, ...),
            correct_answer=(correct_answer_type, ...),
        )

    @classmethod
    def generate_answer_schema(cls, base_schema, **answer_fields):
        field_definitions = dict()
        for field, field_info in answer_fields.items():
            if not isinstance(field_info, tuple):
                field_info = (field_info, ...)
            field_definitions[field] = field_info
        AnswerSchema = create_model(
            f'AnswerSchema{cls.__name__}',
            **field_definitions,
        )
        return create_model(
            f'CheckSchema{cls.__name__}',
            seconds_to_answer=(int, Field(gt=0)),
            answer=(AnswerSchema, ...),
            **{
                name: (field.annotation, field)
                for name, field in base_schema.model_fields.items()
            },
        )

    @classmethod
    def generate_check_endpoint(
        cls, schema: type[BaseModel], **answer_fields
    ) -> tuple[Callable, dict]:
        async def check_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[ExerciseBase, Depends(cls)],
            answer: cls.generate_answer_schema(schema, **answer_fields),
        ):
            return await exercise_builder.check(
                user_id=user['sub'],
                answer=answer.model_dump(include={'answer'})['answer'],
                exercise_request=answer.model_dump(exclude={'answer'}),
            )

        path_options = {
            'responses': {
                **core_schema.NOT_AUTHENTICATED,
                **core_schema.OBJECT_NOT_FOUND,
            },
        }
        return check_endpoint, path_options

    @classmethod
    def as_endpoint(
        cls,
        *,
        router: APIRouter,
        path: str,
        schema: type[BaseModel],
        **answer_fields,
    ):
        build_endpoint, options = cls.generate_build_endpoint(schema)
        router.get(
            path=path,
            response_model=schema,
            name=helper.camel_to_snake(cls.__name__),
            operation_id=cls.__name__,
            **options,
        )(build_endpoint)

        check_endpoint, options = cls.generate_check_endpoint(schema, **answer_fields)
        router.post(
            path=path,
            response_model=cls.generate_exercise_response(),
            name=f'check_{helper.camel_to_snake(cls.__name__)}',
            operation_id=f'check_{cls.__name__}',
            **options,
        )(check_endpoint)

    # end fastapi endpoint methods


class OrderSentenceExercise(ExerciseBase):
    exercise_type = ExerciseType.ORDER_SENTENCE
    instance: type[models.OrderSentence]

    @property
    def distractors(self) -> list:
        max_distractors = len(self.instance.distractors)
        return list(sample(self.instance.distractors, randint(1, max_distractors)))

    def build(self) -> dict:
        sentence = self.instance.sentence + self.distractors
        shuffle(sentence)

        return {'sentence': sentence}

    @property
    def correct_answer(self) -> list[str]:
        return self.instance.sentence

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['sentence']


class ListenTermExercise(ExerciseBase):
    exercise_type = ExerciseType.LISTEN_TERM
    instance: type[models.ListenTerm]

    def build(self) -> dict:
        return {'audio_url': self.instance.audio_url}

    @property
    def correct_answer(self) -> str:
        return self.instance.answer

    def assert_answer(self, answer: dict) -> bool:
        sentence = helper.normalize_text(answer['content'])
        correct_answer = helper.normalize_text(self.correct_answer)
        return sentence == correct_answer


class ListenTermMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.LISTEN_TERM_MCHOICE
    instance: type[models.ListenTermMChoice]

    @property
    def distractors(self) -> dict:
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_id: self.instance.audio_url}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'content': self.instance.content}

    @property
    def correct_answer(self) -> UUID:
        return self.instance.term_id

    def assert_answer(self, answer: dict) -> bool:
        return answer['term_id'] == self.correct_answer


class ListenSentenceExercise(ExerciseBase):
    exercise_type = ExerciseType.LISTEN_SENTENCE
    instance: type[models.ListenSentence]

    def build(self) -> dict:
        return {'audio_url': self.instance.audio_url}

    @property
    def correct_answer(self) -> str:
        return self.instance.answer

    def assert_answer(self, answer: dict) -> bool:
        sentence = helper.normalize_text(answer['content'])
        correct_answer = helper.normalize_text(self.correct_answer)
        return sentence == correct_answer


class SpeakExerciseBase(ExerciseBase):
    MAX_TEXT_DISTANCE = 3

    @classmethod
    def generate_check_endpoint(
        cls, schema: type[BaseModel], **answer_fields
    ) -> tuple[Callable, dict]:
        async def check_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[ExerciseBase, Depends(cls)],
            answer: schema,
            audio: UploadFile,
        ):
            return await exercise_builder.check(
                user_id=user['sub'],
                answer={'audio': await audio.read()},
                exercise_request=answer.model_dump(),
            )

        path_options = {
            'responses': {
                **core_schema.NOT_AUTHENTICATED,
                **core_schema.OBJECT_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST: {
                    'content': {
                        'application/json': {
                            'examples': {
                                'invalid_format': {
                                    'summary': 'InvalidAudioFormat',
                                    'value': {
                                        'detail': 'audio file must be WAV format mono PCM.'
                                    },
                                },
                                'could_not_trascribe': {
                                    'summary': 'CouldNotTrascribe',
                                    'value': {'detail': 'could not trascribe text.'},
                                },
                            }
                        }
                    },
                },
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
                    'content': {
                        'application/json': {
                            'example': {'detail': 'audio_file is too big.'}
                        }
                    },
                },
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    'content': {
                        'application/json': {
                            'example': {
                                'detail': 'something went wrong in audio_file transcription.'
                            }
                        }
                    },
                },
            },
        }
        return check_endpoint, path_options

    @classmethod
    def generate_exercise_response(cls):
        class ExerciseResponseSpeak(BaseModel):
            correct: bool
            correct_answer: str = Field(examples=['i like pizza'])
            user_transcription: str = Field(examples=['i bike pizza'])
            text_diff: list[int] = Field(
                examples=[[1]],
                description='words index diff between correct_answer and user_transcription',
            )

        return ExerciseResponseSpeak

    def assert_answer(self, answer: dict) -> bool:
        return self.MAX_TEXT_DISTANCE >= text.text_distance(
            self.correct_answer, answer['user_transcription']
        )

    async def check(
        self,
        user_id: str,
        answer: dict,
        exercise_request: dict,
    ) -> dict:
        audio = answer.pop('audio')
        user_transcription = trascribe_to_text(
            audio,
            self.correct_answer.split(),
            self.instance.language,
        )
        answer['user_transcription'] = user_transcription
        check_response = await super().check(user_id, answer, exercise_request)
        check_response['user_transcription'] = user_transcription
        check_response['text_diff'] = text.text_diff(
            self.correct_answer, user_transcription
        )
        return check_response


class SpeakTermExercise(SpeakExerciseBase):
    exercise_type = ExerciseType.SPEAK_TERM
    instance: type[models.SpeakTerm]

    def build(self) -> dict:
        return {
            'audio_url': self.instance.audio_url,
            'phonetic': self.instance.phonetic,
        }

    @property
    def correct_answer(self):
        return self.instance.answer


class SpeakSentenceExercise(SpeakExerciseBase):
    exercise_type = ExerciseType.SPEAK_SENTENCE
    instance: type[models.SpeakSentence]

    def build(self) -> dict:
        return {
            'audio_url': self.instance.audio_url,
            'phonetic': self.instance.phonetic,
        }

    @property
    def correct_answer(self):
        return self.instance.answer


class TermSentenceMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_SENTENCE_MCHOICE
    instance: type[models.TermSentenceMChoice]

    @property
    def distractors(self):
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_id: self.instance.answer}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'content': self.instance.sentence}

    @property
    def correct_answer(self) -> UUID:
        return self.instance.term_id

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['term_id']


class TermDefinitionMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_DEFINITION_MCHOICE
    instance: type[models.TermDefinitionMChoice]

    @property
    def distractors(self):
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_definition_id: self.instance.answer}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'content': self.instance.content}

    @property
    def correct_answer(self) -> UUID:
        return self.instance.term_definition_id

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['term_id']


class TermImageMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_IMAGE_MCHOICE
    instance: type[models.TermImageMChoice]

    @property
    def distractors(self):
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_id: self.instance.image_url}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'audio_url': self.instance.audio_url}

    @property
    def correct_answer(self) -> UUID:
        return self.instance.term_id

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['term_id']


class TermImageTextMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_IMAGE_TEXT_MCHOICE
    instance: type[models.TermImageTextMChoice]

    @property
    def distractors(self):
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_id: self.instance.answer}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'image_url': self.instance.image_url}

    @property
    def correct_answer(self) -> UUID:
        return self.instance.term_id

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['term_id']


class TermConnectionExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_CONNECTION
    instance: type[models.TermConnection]

    def build(self) -> dict:
        choices = dict()
        choices.update(helper.sample_dict(self.instance.connections, 4))
        choices.update(helper.sample_dict(self.instance.distractors, 8))
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'content': self.instance.content}

    @property
    def correct_answer(self) -> list[UUID]:
        return list(self.instance.connections.keys())

    def assert_answer(self, answer: dict) -> bool:
        return all([choice in self.correct_answer for choice in answer['choices']])
