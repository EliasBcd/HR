import requests  # pip3 install requests
from pprint import pprint
import requests.exceptions
import urllib.parse


GET = requests.get
POST = requests.post


class BaseOTreeApiError(Exception):
    pass


class OTree4xxOr5xx(BaseOTreeApiError):
    pass


class OTree4xx(OTree4xxOr5xx):
    pass


class OTree5xx(OTree4xxOr5xx):
    pass


class OTreeServerUnreachable(BaseOTreeApiError):
    pass


def call_api(site_url, rest_key, method, *path_parts, **params) -> dict:
    path = '/api/' + '/'.join(path_parts)
    url = urllib.parse.urljoin(site_url, path)
    try:
        resp = method(url, json=params, headers={'otree-rest-key': rest_key})
    except requests.exceptions.RequestException as exc:
        raise OTreeServerUnreachable(f'Could not reach your oTree site at {site_url}')
    if not resp.ok:
        msg = (
            f'Request to "{url}" failed '
            f'with status code {resp.status_code}: {resp.text}'
        )
        if resp.status_code >= 500:
            raise OTree5xx(msg)
        raise OTree4xx(msg)
    return resp.json()
