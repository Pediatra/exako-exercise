import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from exako.auth import current_admin_user, current_user
from exako.main import app, database_client
from exako.settings import settings


async def clear_database():
    collections = await database_client[settings.DATABASE_NAME].list_collection_names()
    for collection in collections:
        await database_client[settings.DATABASE_NAME][collection].delete_many({})


@pytest_asyncio.fixture
async def client():
    with patch.object(settings, 'DATABASE_NAME', 'test_database'):
        async with LifespanManager(app):
            async with AsyncClient(app=app, base_url='http://testserver') as client:
                app.dependency_overrides[current_admin_user] = lambda: {}
                app.dependency_overrides[current_user] = lambda: {}
                yield client
                await clear_database()
            app.dependency_overrides.clear()


@pytest.fixture(scope='session')
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
