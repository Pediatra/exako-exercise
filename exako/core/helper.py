import importlib
import inspect
import re
from random import sample, shuffle
from string import punctuation
from uuid import UUID

from beanie import Document
from fastapi_pagination import Params
from fief_client import FiefAccessTokenInfo
from httpx import AsyncClient

from exako.settings import settings


def shuffle_dict(dict_):
    dict_ = list(dict_.items())
    shuffle(dict_)
    return dict(dict_)


def sample_dict(dict_, n):
    sampled_keys = sample(list(dict_.keys()), n)
    return {key: dict_[key] for key in sampled_keys}


def camel_to_snake(name):
    pattern = re.compile(r'(?<!^)(?<![A-Z])(?=[A-Z])')
    return pattern.sub('_', name).lower()


def normalize_text(text):
    return text.lower().translate(str.maketrans('', '', punctuation)).strip()


def normalize_array_text(array):
    return [normalize_text(item) for item in array]


def register_documents(app_path: str, module_name: str = 'models'):
    module = importlib.import_module(f'{app_path}.{module_name}')
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, Document) and cls != Document
    ]


async def fetch_card_terms(
    user_info: FiefAccessTokenInfo,
    cardsets: list[int],
    params: Params,
) -> list[UUID]:
    result = list()
    cardset_param = ''.join([f'&cardset_id={cardset}' for cardset in cardsets])
    async with AsyncClient() as client:
        response = await client.get(
            settings.API_DOMAIN
            + f'/cardset/cards?page={params.page}&size={params.size}{cardset_param}',
            headers={'Authorization': f'Bearer {user_info["access_token"]}'},
        )
        result.extend([item['id'] for item in response.json()['items']])
    return result
