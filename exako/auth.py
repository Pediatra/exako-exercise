from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth

from exako.settings import settings

fief = FiefAsync(
    settings.FIEF_DOMAIN,
    settings.FIEF_CLIENT_ID,
    settings.FIEF_CLIENT_SCRET,
)

scheme = OAuth2AuthorizationCodeBearer(
    settings.FIEF_DOMAIN + '/authorize',
    settings.FIEF_DOMAIN + '/api/token',
    scopes={'openid': 'openid', 'offline_access': 'offline_access'},
    auto_error=False,
)


auth = FiefAuth(fief, scheme)

current_user = auth.current_user()
current_admin_user = auth.current_user(permissions=['fief:admin'])
