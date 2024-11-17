from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fief_client import FiefUserInfo

from exako.apps.history import schema
from exako.auth import current_user
from exako.core import schema as core_schema
from exako.core.pagination import Page

history_router = APIRouter()


@history_router.get(
    '/info',
    responses={**core_schema.NOT_AUTHENTICATED},
    response_model=schema.HistoryInfo,
    summary='Informações sobre o histórico do usuário.',
)
async def history_info(user: Annotated[FiefUserInfo, Depends(current_user)]):
    pass


@history_router.get(
    '/',
    responses={**core_schema.NOT_AUTHENTICATED},
    summary='Consulta ao histórico do usuário.',
)
async def list_history(
    user: Annotated[FiefUserInfo, Depends(current_user)],
) -> Page[schema.HistoryRead]:
    pass


@history_router.get(
    '/statistic',
    responses={**core_schema.NOT_AUTHENTICATED},
    response_model=schema.HistoryStatistic,
    summary='Estatística sobre o histórico do usuário.',
)
async def history_statistic(
    user: Annotated[FiefUserInfo, Depends(current_user)],
    filter_params: Annotated[schema.HistoryStatisticQuery, Query()],
):
    pass
