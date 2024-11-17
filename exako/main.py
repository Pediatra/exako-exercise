from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import add_pagination
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from starlette.responses import JSONResponse

from exako.apps.computed.router import computed_router
from exako.apps.exercise.router import exercise_router
from exako.apps.history.router import history_router
from exako.core.helper import register_documents
from exako.settings import settings

database_client = AsyncIOMotorClient(settings.DATABASE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=database_client[settings.DATABASE_NAME],
        document_models=[
            *register_documents('exako.apps.exercise'),
            *register_documents('exako.apps.computed'),
        ],
    )
    yield


app = FastAPI(lifespan=lifespan)

add_pagination(app)

app.include_router(exercise_router, prefix='/exercise', tags=['exercise'])
app.include_router(
    computed_router, prefix='/exercise/computed', tags=['computed exercise']
)
app.include_router(
    history_router, prefix='/exercise/history', tags=['exercise history']
)


@app.exception_handler(ValidationError)
async def validation_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={'detail': jsonable_encoder(exc.errors())},
    )
