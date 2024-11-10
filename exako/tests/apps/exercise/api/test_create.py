import json
from uuid import uuid4

import pytest

from exako.apps.exercise.models import Exercise
from exako.main import app
from exako.tests.factories import exercise as exercise_factory

pytestmark = pytest.mark.asyncio


create_exercise_router = app.url_path_for('create_exercise')

parametrize_exercies = pytest.mark.parametrize(
    'factory',
    [
        exercise_factory.OrderSentenceFactory,
        exercise_factory.ListenTermFactory,
        exercise_factory.ListenSentenceFactory,
        exercise_factory.ListenTermMChoiceFactory,
        exercise_factory.SpeakTermFactory,
        exercise_factory.SpeakSentenceFactory,
        exercise_factory.TermSentenceMChoiceFactory,
        exercise_factory.TermDefinitionMChoiceFactory,
        exercise_factory.TermImageMChoiceFactory,
        exercise_factory.TermImageTextMChoiceFactory,
        exercise_factory.TermConnectionFactory,
    ],
)


@parametrize_exercies
async def test_create_exercise(client, factory):
    payload = factory.generate_payload()

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 201
    assert await Exercise.get(response.json()['id'], with_children=True)


async def test_create_order_sentence_redundant_distractors(client):
    payload = exercise_factory.OrderSentenceFactory.generate_payload(
        distractors=['test', 'test', 'a', 'a']
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 201
    exercise = await Exercise.get(response.json()['id'], with_children=True)
    assert exercise.distractors == ['test', 'a']


@pytest.mark.parametrize('conflict_str', ['test', '!test.', 'TEST', '    test '])
async def test_create_order_sentence_exercise_invalid_distractors(client, conflict_str):
    payload = exercise_factory.OrderSentenceFactory.generate_payload(
        sentence=[conflict_str, 'a', 'testing'],
        distractors=['test', 'hola', 'caixa'],
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 201
    exercise = await Exercise.get(response.json()['id'], with_children=True)
    assert exercise.distractors == ['hola', 'caixa']


@parametrize_exercies
async def test_create_exercise_already_exists(client, factory):
    payload = factory.generate_payload()
    await factory(**json.loads(payload))

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 409


@pytest.mark.parametrize(
    'factory',
    [
        exercise_factory.ListenTermFactory,
        exercise_factory.ListenTermMChoiceFactory,
        exercise_factory.ListenSentenceFactory,
        exercise_factory.SpeakTermFactory,
        exercise_factory.SpeakSentenceFactory,
        exercise_factory.TermImageMChoiceFactory,
    ],
)
async def test_create_exercise_invalid_audio_url(client, factory):
    payload = factory.generate_payload(audio_url='https://test.com')

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert 'invalid audio_url.' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize(
    'factory',
    [
        exercise_factory.TermImageMChoiceFactory,
        exercise_factory.TermImageTextMChoiceFactory,
    ],
)
async def test_create_exercise_invalid_image_url(client, factory):
    payload = factory.generate_payload(image_url='https://test.com')

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert 'invalid image_url.' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize(
    'factory',
    [
        exercise_factory.ListenTermMChoiceFactory,
        exercise_factory.TermSentenceMChoiceFactory,
        exercise_factory.TermDefinitionMChoiceFactory,
        exercise_factory.TermImageMChoiceFactory,
        exercise_factory.TermImageTextMChoiceFactory,
        exercise_factory.TermConnectionFactory,
    ],
)
async def test_create_exercise_invalid_distractors_term_reference(client, factory):
    term_reference = uuid4()
    distractors = exercise_factory.generate_alternatives(8)
    distractors.update({term_reference: 'waj4ihpah2qoa'})
    payload = factory.generate_payload(
        term_reference=term_reference,
        distractors=distractors,
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert (
        'term_reference cannot be in distractors.'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize(
    'factory',
    [
        exercise_factory.ListenTermMChoiceFactory,
        exercise_factory.TermSentenceMChoiceFactory,
        exercise_factory.TermDefinitionMChoiceFactory,
        exercise_factory.TermImageMChoiceFactory,
        exercise_factory.TermImageTextMChoiceFactory,
        exercise_factory.TermConnectionFactory,
    ],
)
async def test_create_exercise_invalid_distractors_term_id(client, factory):
    term_id = uuid4()
    distractors = exercise_factory.generate_alternatives(8)
    distractors.update({term_id: 'waj4ihpah2qoa'})
    payload = factory.generate_payload(term_id=term_id, distractors=distractors)

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert 'term_id cannot be in distractors.' in response.json()['detail'][0]['msg']


async def test_create_connection_exercise_invalid_connection_term_reference(client):
    term_reference = uuid4()
    connections = exercise_factory.generate_alternatives(8)
    connections.update({term_reference: 'waj4ihpah2qoa'})
    payload = exercise_factory.TermConnectionFactory.generate_payload(
        term_reference=term_reference, connections=connections
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert (
        'term_reference cannot be in connections.'
        in response.json()['detail'][0]['msg']
    )


async def test_create_connection_exercise_invalid_connection_term_id(client):
    term_id = uuid4()
    connections = exercise_factory.generate_alternatives(8)
    connections.update({term_id: 'waj4ihpah2qoa'})
    payload = exercise_factory.TermConnectionFactory.generate_payload(
        term_id=term_id, connections=connections
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert 'term_id cannot be in connections.' in response.json()['detail'][0]['msg']


async def test_create_connection_exercise_intersection_in_connections_distractors(
    client,
):
    connections = exercise_factory.generate_alternatives(8)
    payload = exercise_factory.TermConnectionFactory.generate_payload(
        connections=connections,
        distractors=connections,
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert (
        'an intersection was found between distractors and connections.'
        in response.json()['detail'][0]['msg']
    )