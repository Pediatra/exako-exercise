from typing import Annotated

from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination.ext.beanie import paginate
from fief_client import FiefUserInfo
from pymongo.errors import DuplicateKeyError

from exako.apps.computed import schema
from exako.apps.computed.models import ExerciseComputed, computed_exercise_map
from exako.auth import current_admin_user
from exako.core import schema as core_schema
from exako.core.constants import ExerciseType, Language
from exako.core.pagination import Page

computed_router = APIRouter()


@computed_router.post(
    path='/',
    status_code=201,
    response_model=schema.ExerciseCreateRead,
    responses={
        **core_schema.PERMISSION_DENIED,
        status.HTTP_409_CONFLICT: {
            'description': 'O exercício específicado já existe.',
            'content': {
                'application/json': {'example': {'detail': 'exercise already exists.'}}
            },
        },
    },
    summary='Criar um novo exercício.',
    description='Endpoint criado para criar um novo tipo de exercício baseado em um termo existente.',
)
async def create_computed_exercise(
    user: Annotated[FiefUserInfo, Depends(current_admin_user)],
    exercise_schema: schema.ExerciseCreateBase,
):
    exercise_model = computed_exercise_map[exercise_schema.type]
    try:
        return await exercise_model.update_or_insert(**exercise_schema.model_dump())
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='exercise already exists.',
        )


@computed_router.get(
    '/',
    responses={**core_schema.PERMISSION_DENIED},
    summary='Listar os exercícios pré-computados.',
)
async def list_computed_exercises(
    user: Annotated[FiefUserInfo, Depends(current_admin_user)],
    type: ExerciseType,
    language: Language,
) -> Page[schema.ExerciseCreateRead]:
    return paginate(
        ExerciseComputed.find_all(
            In(ExerciseComputed.type, type),
            In(ExerciseComputed.language, language),
        )
    )
