from typing import ClassVar, Type
from uuid import UUID

from beanie import Document
from pydantic import ValidationError

from exako.apps.exercise import models
from exako.core.constants import ExerciseType, Language


class ExerciseComputed(Document):
    language: Language
    type: ExerciseType

    model: ClassVar[models.Exercise] = models.Exercise

    @classmethod
    def validate_exercise_data(cls, **data):
        cls.model_validate(data)
        try:
            cls.model.model_validate(data)
        except ValidationError as e:
            errors = e.errors()
            missing_fields = [
                error for error in errors if error.get('type') == 'missing'
            ]
            # raises error if it was not caused only by missing fields
            if e.error_count() > len(missing_fields):
                line_errors = [error for error in errors if error not in missing_fields]
                raise ValidationError.from_exception_data(
                    cls.model.__name__, line_errors
                )

    @classmethod
    async def insert_exercise(
        cls, computed: Type['ExerciseComputed']
    ) -> Type['ExerciseComputed'] | Type[models.Exercise]:
        instance_data = computed.model_dump()
        try:
            exercise = cls.model(**instance_data)
            await exercise.insert()
            await computed.delete()
            return exercise
        except ValidationError:
            return computed  # ignoring missing field error to keep saving partial exercises

    @classmethod
    async def update_or_insert(
        cls, **data: dict
    ) -> Type['ExerciseComputed'] | Type[models.Exercise]:
        term_reference = data.pop('term_reference')
        data[cls.term_reference] = term_reference

        computed = await ExerciseComputed.find(
            {'type': data['type'], cls.term_reference: term_reference},
            with_children=True,
        ).first_or_none()

        if computed is None:
            cls.validate_exercise_data(**data)
            computed = await cls(**data).insert()
        else:
            cls.validate_exercise_data(**data | computed.model_dump(exclude_none=True))
            computed = await computed.update({'$set': data})
        return await cls.insert_exercise(computed)

    class Settings:
        is_root = True
        name = 'exercises_computed'


class OrderSentenceComputed(ExerciseComputed):
    sentence: list[str] | None = None
    distractors: list[str] | None = None
    term_example_id: UUID

    term_reference: ClassVar[str] = 'term_example_id'
    model: ClassVar[models.OrderSentence] = models.OrderSentence


class ListenTermComputed(ExerciseComputed):
    audio_url: str | None = None
    answer: str | None = None
    term_id: UUID

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.ListenTerm] = models.ListenTerm


class ListenTermMChoiceComputed(ExerciseComputed):
    audio_url: str | None = None
    content: str | None = None
    term_id: UUID
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.ListenTermMChoice] = models.ListenTermMChoice


class ListenSentenceComputed(ExerciseComputed):
    audio_url: str | None = None
    answer: str | None = None
    term_example_id: UUID

    term_reference: ClassVar[str] = 'term_example_id'
    model: ClassVar[models.ListenSentence] = models.ListenSentence


class SpeakTermComputed(ExerciseComputed):
    audio_url: str | None = None
    phonetic: str | None = None
    content: str | None = None
    term_id: UUID

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.SpeakTerm] = models.SpeakTerm


class SpeakSentenceComputed(ExerciseComputed):
    audio_url: str | None = None
    phonetic: str | None = None
    content: str | None = None
    term_example_id: UUID

    term_reference: ClassVar[str] = 'term_example_id'
    model: ClassVar[models.SpeakSentence] = models.SpeakSentence


class TermSentenceMChoiceComputed(ExerciseComputed):
    sentence: str | None = None
    answer: str | None = None
    term_id: UUID
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.TermSentenceMChoice] = models.TermSentenceMChoice


class TermDefinitionMChoiceComputed(ExerciseComputed):
    content: str | None = None
    answer: str | None = None
    term_id: UUID
    term_definition_id: UUID
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_definition_id'
    model: ClassVar[models.TermDefinitionMChoice] = models.TermDefinitionMChoice


class TermImageMChoiceComputed(ExerciseComputed):
    image_url: str | None = None
    audio_url: str | None = None
    term_id: UUID
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.TermImageMChoice] = models.TermImageMChoice


class TermImageTextMChoiceComputed(ExerciseComputed):
    image_url: str | None = None
    answer: str | None = None
    term_id: UUID
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.TermImageTextMChoice] = models.TermImageTextMChoice


class TermConnectionComputed(ExerciseComputed):
    content: str | None = None
    term_id: UUID
    connections: dict[UUID, str] | None = None
    distractors: dict[UUID, str] | None = None

    term_reference: ClassVar[str] = 'term_id'
    model: ClassVar[models.TermConnection] = models.TermConnection


computed_exercise_map: dict[ExerciseType, type[ExerciseComputed]] = {
    ExerciseType.ORDER_SENTENCE: OrderSentenceComputed,
    ExerciseType.LISTEN_TERM: ListenTermComputed,
    ExerciseType.LISTEN_SENTENCE: ListenSentenceComputed,
    ExerciseType.LISTEN_TERM_MCHOICE: ListenTermMChoiceComputed,
    ExerciseType.SPEAK_TERM: SpeakTermComputed,
    ExerciseType.SPEAK_SENTENCE: SpeakSentenceComputed,
    ExerciseType.TERM_SENTENCE_MCHOICE: TermSentenceMChoiceComputed,
    ExerciseType.TERM_DEFINITION_MCHOICE: TermDefinitionMChoiceComputed,
    ExerciseType.TERM_IMAGE_MCHOICE: TermImageMChoiceComputed,
    ExerciseType.TERM_IMAGE_TEXT_MCHOICE: TermImageTextMChoiceComputed,
    ExerciseType.TERM_CONNECTION: TermConnectionComputed,
}