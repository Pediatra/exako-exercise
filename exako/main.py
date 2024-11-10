from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from motor.motor_asyncio import AsyncIOMotorClient

from exako.apps.exercise.router import exercise_router
from exako.settings import settings

database_client = AsyncIOMotorClient(settings.DATABASE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=database_client[settings.DATABASE_NAME],
        document_models=[
            'exako.apps.exercise.models.Exercise',
            'exako.apps.exercise.models.OrderSentence',
            'exako.apps.exercise.models.ListenTerm',
            'exako.apps.exercise.models.ListenTermMChoice',
            'exako.apps.exercise.models.ListenSentence',
            'exako.apps.exercise.models.SpeakTerm',
            'exako.apps.exercise.models.SpeakSentence',
            'exako.apps.exercise.models.TermSentenceMChoice',
            'exako.apps.exercise.models.TermDefinitionMChoice',
            'exako.apps.exercise.models.TermImageMChoice',
            'exako.apps.exercise.models.TermImageTextMChoice',
            'exako.apps.exercise.models.TermConnection',
        ],
    )
    yield


app = FastAPI(lifespan=lifespan)

add_pagination(app)

app.include_router(exercise_router, prefix='/exercise')
