from abc import ABC, abstractmethod
from random import randint, sample, shuffle
from typing import Annotated, Any, Callable

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fief_client import FiefUserInfo
from pydantic import BaseModel, Field, create_model

from exako.apps.exercise import models
from exako.apps.exercise.schema import ExerciseResponse
from exako.auth import current_user
from exako.core import helper
from exako.core import schema as core_schema
from exako.core.constants import ExerciseType


class ExerciseBase(ABC):
    exercise_type: ExerciseType
    instance: type[models.Exercise]

    def __init__(
        self,
        exercise_id: PydanticObjectId,
    ):
        self.instance = models.Exercise.find_one(
            {
                'id': exercise_id,
                'type': self.exercise_type,
            },
            with_children=True,
        )
        if self.instance is None:
            raise HTTPException(status_code=404, detail='exercise not found.')

    @abstractmethod
    def build(self) -> dict: ...

    @property
    @abstractmethod
    def correct_answer(self) -> Any: ...

    @abstractmethod
    def assert_answer(self, answer: dict) -> bool: ...

    def check(self, user: FiefUserInfo, answer: dict, exercise_request: dict) -> dict:
        correct = self.assert_answer(answer)
        check_response = {
            'correct': correct,
            'correct_answer': self.correct_answer,
        }
        # self.history_repository.create( TODO
        #     exercise=self.instance,
        #     user=user['sub'],
        #     correct=correct,
        #     response={**answer, **check_response},
        #     request=exercise_request,
        # )
        return check_response

    @classmethod
    def generate_build_endpoint(cls, exercise_schema: type[BaseModel]) -> Callable:
        def build_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[type[ExerciseBase], Depends(cls)],
        ):
            return exercise_schema(**exercise_builder.build())

        return build_endpoint

    @classmethod
    def generate_check_endpoint(
        cls, schema: type[BaseModel], **answer_fields
    ) -> Callable:
        field_definitions = dict()
        for field, field_info in answer_fields.items():
            if not isinstance(field_info, tuple):
                field_info = (field_info, ...)
            field_definitions[field] = field_info
        AnswerSchema = create_model(
            f'AnswerSchema{cls.__name__}',
            **field_definitions,
        )
        CheckSchema = create_model(
            f'CheckSchema{cls.__name__}',
            time_to_answer=(int, Field(gt=0)),
            answer=(AnswerSchema, ...),
            **{
                name: (field.annotation, field)
                for name, field in schema.model_fields.items()
            },
        )

        def check_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[type[ExerciseBase], Depends(cls)],
            answer: CheckSchema,
        ):
            return ExerciseResponse(
                **exercise_builder.check(
                    user,
                    answer=answer.model_dump()['answer'],
                    exercise_request=answer.model_dump(exclude={'answer'}),
                )
            )

        return check_endpoint

    @classmethod
    def as_endpoint(
        cls,
        *,
        router: APIRouter,
        path: str,
        schema: type[BaseModel],
        **answer_fields,
    ):
        router.get(
            path=path,
            response_model=schema,
            responses={
                **core_schema.NOT_AUTHENTICATED,
                **core_schema.OBJECT_NOT_FOUND,
            },
            name=helper.camel_to_snake(cls.__name__),
            operation_id=cls.__name__,
        )(cls.generate_build_endpoint(schema))

        router.post(
            path=path,
            response_model=ExerciseResponse,
            responses={
                **core_schema.NOT_AUTHENTICATED,
                **core_schema.OBJECT_NOT_FOUND,
            },
            name=f'check_{helper.camel_to_snake(cls.__name__)}',
            operation_id=f'check_{cls.__name__}',
        )(cls.generate_check_endpoint(schema, **answer_fields))


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
    def correct_answer(self):
        return self.instance.sentence

    def assert_answer(self, answer: dict) -> bool:
        return self.correct_answer == answer['sentence']


class ListenTermExercise(ExerciseBase):
    exercise_type = ExerciseType.LISTEN_TERM
    instance: type[models.ListenTerm]

    def build(self) -> dict:
        return {'audio_url': self.instance.audio_url}

    @property
    def correct_answer(self):
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
    def correct_answer(self):
        return self.instance.term_id

    def assert_answer(self, answer: dict) -> bool:
        return answer['term_id'] == self.correct_answer


class ListenSentenceExercise(ExerciseBase):
    exercise_type = ExerciseType.LISTEN_SENTENCE
    instance: type[models.ListenSentence]

    def build(self) -> dict:
        return {'audio_url': self.instance.audio_url}

    @property
    def correct_answer(self):
        return self.instance.answer

    def assert_answer(self, answer: dict) -> bool:
        sentence = helper.normalize_text(answer['content'])
        correct_answer = helper.normalize_text(self.correct_answer)
        return sentence == correct_answer


class SpeakTermExercise(ExerciseBase):
    exercise_type = ExerciseType.SPEAK_TERM
    instance: type[models.SpeakTerm]

    def build(self) -> dict:
        return {
            'audio_url': self.instance.audio_url,
            'phonetic': self.instance.phonetic,
            'content': self.instance.content,
        }

    @property
    def correct_answer(self):
        return self.instance.content

    def assert_answer(self, answer: dict) -> bool:
        # TODO: SpeechToText API
        return True

    def check(self, user: FiefUserInfo, answer: dict, exercise_request: dict) -> dict:
        answer.pop('audio')  # TODO: SpeechToText API
        return super().check(user, answer, exercise_request)

    @classmethod
    def _generate_check_endpoint(cls, CheckSchema: type[BaseModel], **answer_fields):
        def check_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[type[ExerciseBase], Depends(cls)],
            answer: CheckSchema,
            audio: UploadFile,
        ):
            return ExerciseResponse(
                **exercise_builder.check(
                    user=user,
                    answer={'audio': audio},
                    exercise_request=answer.model_dump(),
                )
            )

        return check_endpoint


class SpeakSentenceExercise(ExerciseBase):
    exercise_type = ExerciseType.SPEAK_SENTENCE
    instance: type[models.SpeakSentence]

    def build(self) -> dict:
        return {
            'audio_url': self.instance.audio_url,
            'phonetic': self.instance.phonetic,
            'content': self.instance.content,
        }

    @property
    def correct_answer(self):
        return self.instance.content

    def assert_answer(self, answer: dict) -> bool:
        # TODO: SpeechToText API
        return True

    def check(self, user: FiefUserInfo, answer: dict, exercise_request: dict) -> dict:
        answer.pop('audio')  # TODO: SpeechToText API
        return super().check(user, answer, exercise_request)

    @classmethod
    def _generate_check_endpoint(cls, CheckSchema: type[BaseModel], **answer_fields):
        def check_endpoint(
            user: Annotated[FiefUserInfo, Depends(current_user)],
            exercise_builder: Annotated[type[ExerciseBase], Depends(cls)],
            answer: CheckSchema,
            audio: UploadFile,
        ):
            return ExerciseResponse(
                **exercise_builder.check(
                    user=user,
                    answer={'audio': audio},
                    exercise_request=answer.model_dump(),
                )
            )

        return check_endpoint


class TermSentenceMChoiceExercise(ExerciseBase):
    exercise_type = ExerciseType.TERM_SENTENCE_MCHOICE
    instance: type[models.TermSentenceMChoice]

    @property
    def distractors(self):
        return helper.sample_dict(self.instance.distractors, 3)

    def build(self) -> dict:
        choices = {self.instance.term_id: self.instance.conetnt}
        choices.update(self.distractors)
        choices = helper.shuffle_dict(choices)

        return {'choices': choices, 'content': self.instance.sentence}

    @property
    def correct_answer(self):
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
    def correct_answer(self):
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
    def correct_answer(self):
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
    def correct_answer(self):
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
    def correct_answer(self):
        return self.instance.connections

    def assert_answer(self, answer: dict) -> bool:
        return all([choice in self.correct_answer for choice in answer['choices']])
