from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def set_url_params(url: str, **params: Any | list[Any]) -> str:
    filtered_params = {
        k: v if isinstance(v, list) else [v] for k, v in params.items() if v is not None
    }

    parsed_url = urlparse(url)
    current_params = parse_qs(parsed_url.query)

    for key, value in filtered_params.items():
        if key in current_params:
            current_params[key].extend(value)
        else:
            current_params[key] = value

    new_query = urlencode(current_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))
