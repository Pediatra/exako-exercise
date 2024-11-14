from random import random
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Params
from fastapi_pagination.ext.beanie import paginate
from fief_client import FiefAccessTokenInfo
from pydantic import Field

from exako.apps.exercise import builder, schema
from exako.apps.exercise.models import Exercise
from exako.auth import current_user
from exako.core import schema as core_schema
from exako.core.constants import ExerciseType, Language, Level
from exako.core.pagination import Page

exercise_router = APIRouter()


@exercise_router.get(
    path='/',
    responses={**core_schema.NOT_AUTHENTICATED},
    summary='Consulta exercícios sobre termos disponíveis.',
    description='Endpoint para retornar exercícios sobre termos. Os exercícios serão montados com termos aleatórios, a menos que seja específicado o cardset_id.',
)
async def list_exercise(
    user: Annotated[FiefAccessTokenInfo, Depends(current_user)],
    language: Annotated[list[Language], Query(...)],
    params: Annotated[Params, Depends()],
    type: list[ExerciseType] | None = Query(default=[ExerciseType.RANDOM]),
    level: list[Level] | None = Query(
        default=None, description='Filtar por dificuldade do termo.'
    ),
    cardset: list[int] | None = Query(
        default=None, description='Filtrar por conjunto de cartas.'
    ),
    seed: float | None = Query(default_factory=random, le=1, ge=0),
) -> Page[schema.ExerciseRead]:
    return await paginate(
        Exercise.list(
            language=language,
            type=type,
            level=level,
            cardset=cardset,
            seed=seed,
            user=user,
            params=params,
        ),
        params=params,
    )


builder.OrderSentenceExercise.as_endpoint(
    router=exercise_router,
    path='/order-sentence/{exercise_id}',
    schema=schema.OrderSentenceRead,
    sentence=list[str],
)

builder.ListenTermExercise.as_endpoint(
    router=exercise_router,
    path='/listen-term/{exercise_id}',
    schema=schema.ListenRead,
    content=str,
)

builder.ListenTermMChoiceExercise.as_endpoint(
    router=exercise_router,
    path='/listen-term-mchoice/{exercise_id}',
    schema=schema.ListenMChoiceRead,
    term_id=int,
)

builder.ListenSentenceExercise.as_endpoint(
    router=exercise_router,
    path='/listen-sentence/{exercise_id}',
    schema=schema.ListenRead,
    content=str,
)

builder.SpeakTermExercise.as_endpoint(
    router=exercise_router,
    path='/speak-term/{exercise_id}',
    schema=schema.SpeakRead,
)

builder.SpeakSentenceExercise.as_endpoint(
    router=exercise_router,
    path='/speak-sentence/{exercise_id}',
    schema=schema.SpeakRead,
)

builder.TermSentenceMChoiceExercise.as_endpoint(
    router=exercise_router,
    path='/term-mchoice/{exercise_id}',
    schema=schema.TermMChoiceRead,
    term_id=int,
)

builder.TermDefinitionMChoiceExercise.as_endpoint(
    router=exercise_router,
    path='/definition-mchoice/{exercise_id}',
    schema=schema.TermMChoiceRead,
    term_id=int,
)

builder.TermImageMChoiceExercise.as_endpoint(
    router=exercise_router,
    path='/term-image-mchoice/{exercise_id}',
    schema=schema.ImageMChoiceRead,
    term_id=int,
)

builder.TermImageTextMChoiceExercise.as_endpoint(
    router=exercise_router,
    path='/term-image-text-mchoice/{exercise_id}',
    schema=schema.TextImageMChoiceRead,
    term_id=int,
)

builder.TermConnectionExercise.as_endpoint(
    router=exercise_router,
    path='/term-connection/{exercise_id}',
    schema=schema.TextConnectionRead,
    choices=(list[int], Field(min_length=4, max_length=4)),
)
