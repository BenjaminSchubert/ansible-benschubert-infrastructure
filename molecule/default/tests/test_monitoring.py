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


def test_services_are_up(
    hostvars: dict[str, Any],
    session: requests.Session,
    authentik_credentials: tuple[str, str],
) -> None:
    resp = session.get(
        f"https://{hostvars['monitoring_mimir_hostname']}/prometheus/api/v1/query",
        params={"query": "up"},
        allow_redirects=False,
        auth=authentik_credentials,
        timeout=10,
    )
    print(resp.text)
    assert resp.status_code == HTTPStatus.OK
    result = resp.json()
    assert result["status"] == "success"
    entries = {
        (r["metric"]["instance"], r["value"][1])
        for r in result["data"]["result"]
    }
    assert entries == {
        ("agent", "1"),
        ("grafana", "1"),
        ("mimir", "1"),
        ("postgresql://monitoring-grafana-postgres:5432/grafana", "1"),
    }


def test_postgres_databases_are_up(
    hostvars: dict[str, Any],
    session: requests.Session,
    authentik_credentials: tuple[str, str],
) -> None:
    resp = session.get(
        f"https://{hostvars['monitoring_mimir_hostname']}/prometheus/api/v1/query",
        params={"query": "pg_up"},
        allow_redirects=False,
        auth=authentik_credentials,
        timeout=10,
    )
    print(resp.text)
    assert resp.status_code == HTTPStatus.OK
    result = resp.json()
    assert result["status"] == "success"
    entries = {
        (r["metric"]["instance"], r["value"][1])
        for r in result["data"]["result"]
    }
    assert entries == {
        ("postgresql://monitoring-grafana-postgres:5432/grafana", "1"),
    }
