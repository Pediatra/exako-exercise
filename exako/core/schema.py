from fastapi import status

OBJECT_NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'content': {'application/json': {'example': {'detail': 'object not found.'}}},
    },
}

NOT_AUTHENTICATED = {
    status.HTTP_401_UNAUTHORIZED: {
        'content': {
            'application/json': {'example': {'detail': 'invalid credentials.'}}
        },
    },
}

PERMISSION_DENIED = {
    **NOT_AUTHENTICATED,
    status.HTTP_403_FORBIDDEN: {
        'content': {
            'application/json': {'example': {'detail': 'not enough permissions.'}}
        },
    },
}
