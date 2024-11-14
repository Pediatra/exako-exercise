import json
from uuid import uuid4

import pytest

from exako.apps.exercise.models import Exercise
from exako.main import app
from exako.tests.factories import exercise as exercise_factory

pytestmark = pytest.mark.asyncio


create_exercise_router = app.url_path_for('create_computed_exercise')


partial_parametrize_exercies = pytest.mark.parametrize(
    'factory, exclude',
    [
        (exercise_factory.OrderSentenceFactory, 'distractors'),
        (exercise_factory.ListenTermFactory, 'audio_url'),
        (exercise_factory.ListenSentenceFactory, 'audio_url'),
        (exercise_factory.ListenTermMChoiceFactory, 'audio_url'),
        (exercise_factory.SpeakTermFactory, 'audio_url'),
        (exercise_factory.SpeakSentenceFactory, 'audio_url'),
        (exercise_factory.TermSentenceMChoiceFactory, 'distractors'),
        (exercise_factory.TermDefinitionMChoiceFactory, 'distractors'),
        (exercise_factory.TermImageMChoiceFactory, 'distractors'),
        (exercise_factory.TermImageTextMChoiceFactory, 'distractors'),
        (exercise_factory.TermConnectionFactory, 'distractors'),
    ],
)


@partial_parametrize_exercies
async def test_create_computed_exercise(client, factory, exclude):
    payload = factory.generate_payload(exclude={exclude})

    response = await client.post(create_exercise_router, content=payload)

    content = response.json()
    assert response.status_code == 201
    assert await Exercise.get(content['id'], with_children=True) is None
    assert await factory.find_computed(payload) is not None


@partial_parametrize_exercies
async def test_create_computed_exercise_then_update_computed_that_creates_new_exercise(
    client, factory, exclude
):
    term_reference = uuid4()
    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        exclude={exclude},
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 201
    assert await Exercise.get(response.json()['id'], with_children=True) is None
    computed = await factory.find_computed(payload)
    assert computed is not None
    assert getattr(computed, exclude, None) is None

    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        include={exclude, 'type', factory.term_reference},
    )
    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 201
    assert await Exercise.get(response.json()['id'], with_children=True) is not None
    assert await factory.find_computed(payload) is None


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
async def test_create_computed_exercise_invalid_audio_url(client, factory):
    term_reference = uuid4()
    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        exclude={'audio_url'},
    )

    await factory.computed(
        **{factory.term_reference: term_reference}, **json.loads(payload)
    ).insert()

    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        audio_url='https://example.com',
        include={'audio_url', 'type', factory.term_reference},
    )
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
async def test_create_computed_exercise_invalid_image_url(client, factory):
    term_reference = uuid4()
    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        exclude={'image_url'},
    )

    await factory.computed(
        **{factory.term_reference: term_reference}, **json.loads(payload)
    ).insert()

    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        image_url='https://example.com',
        include={'image_url', 'type', factory.term_reference},
    )

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
async def test_create_computed_exercise_invalid_distractors_term_reference(
    client, factory
):
    term_reference = uuid4()
    payload = factory.generate_payload(
        **{factory.term_reference: term_reference},
        exclude={'distractors'},
    )

    await factory.computed(
        **{factory.term_reference: term_reference}, **json.loads(payload)
    ).insert()

    distractors = exercise_factory.generate_alternatives(16)
    distractors.update({term_reference: 'waj4ihpah2qoa'})
    payload = factory.generate_payload(
        **{factory.term_reference: term_reference, 'distractors': distractors},
        include={'distractors', 'type', factory.term_reference},
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert (
        f'{factory.term_reference} cannot be in distractors.'
        in response.json()['detail'][0]['msg']
    )


async def test_create_computed_exercise_connection_intersection_in_connections_distractors(
    client,
):
    term_reference = uuid4()
    connections = exercise_factory.generate_alternatives(16)
    payload = exercise_factory.TermConnectionFactory.generate_payload(
        **{'term_id': term_reference},
        connections=connections,
        exclude={'distractors'},
    )

    await exercise_factory.TermConnectionFactory.computed(
        **{'term_id': term_reference}, **json.loads(payload)
    ).insert()

    payload = exercise_factory.TermConnectionFactory.generate_payload(
        **{'term_id': term_reference},
        distractors=connections,
        include={'distractors', 'type', 'term_id'},
    )

    response = await client.post(create_exercise_router, content=payload)

    assert response.status_code == 422
    assert (
        'an intersection was found between distractors and connections.'
        in response.json()['detail'][0]['msg']
    )
