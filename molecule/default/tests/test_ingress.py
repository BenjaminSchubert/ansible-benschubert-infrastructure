from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import requests


def test_ingress_access_http_redirects_to_https(http_port: int) -> None:
    resp = requests.get(
        f"http://localhost:{http_port}",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.MOVED_PERMANENTLY


def test_ingress_access_https(https_port: int) -> None:
    resp = requests.get(
        f"https://localhost:{https_port}",
        verify=False,  # noqa:S501
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_traefik_dashboard_requires_authentication(
    hostvars: dict[str, Any],
    session: requests.Session,
) -> None:
    resp = session.get(
        f"https://{hostvars['ingress_traefik_dashboard_hostname']}",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert (
        urlparse(resp.headers["Location"]).hostname
        == hostvars["auth_authentik_hostname"]
    )
