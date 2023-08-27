from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import requests


def test_can_access_grafana(
    hostvars: dict[str, Any], session: requests.Session
) -> None:
    resp = session.get(
        f"https://{hostvars['monitoring_grafana_hostname']}/",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert urlparse(resp.headers["Location"]).path == "/login"


def test_can_access_mimir(
    hostvars: dict[str, Any], session: requests.Session
) -> None:
    resp = session.get(
        f"https://{hostvars['monitoring_mimir_hostname']}/",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert (
        urlparse(resp.headers["Location"]).hostname
        == hostvars["auth_authentik_hostname"]
    )
    assert (
        urlparse(resp.headers["Location"]).path == "/application/o/authorize/"
    )
