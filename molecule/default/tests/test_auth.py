from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import pytest
import requests
import yaml


def test_can_access(
    hostvars: dict[str, Any],
    session: requests.Session,
) -> None:
    resp = session.get(
        f"https://{hostvars['auth_authentik_hostname']}",
        allow_redirects=False,
        timeout=10,
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert (
        urlparse(resp.headers["Location"]).path
        == "/flows/-/default/authentication/"
    )


def test_no_tasks_failed(
    hostvars: dict[str, Any],
    session: requests.Session,
) -> None:
    resp = session.get(
        f"https://{hostvars['auth_authentik_hostname']}/api/v3/tasks/tasks/?ordering=mtime&page_size=100000",
        headers={
            "Authorization": f"Bearer {hostvars['auth_authentik_superadmin_bootstrap_token']}"
        },
        allow_redirects=False,
        timeout=10,
    )

    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["pagination"]["total_pages"] == 1

    results = {}
    for task in data["results"]:
        if task["aggregated_status"] == "successful":
            continue
        results[task["uid"]] = {
            "description": task["description"],
            "status": task["aggregated_status"],
        }

    unsuccessful = {k: v for k, v in results.items() if v["status"] != "info"}
    assert unsuccessful == {}


def test_all_blueprints_applied(
    hostvars: dict[str, Any],
    session: requests.Session,
) -> None:
    resp = session.get(
        f"https://{hostvars['auth_authentik_hostname']}/api/v3/managed/blueprints/",
        headers={
            "Authorization": f"Bearer {hostvars['auth_authentik_superadmin_bootstrap_token']}"
        },
        allow_redirects=False,
        timeout=10,
    )

    assert resp.status_code == HTTPStatus.OK
    print(yaml.dump(resp.json()))

    failed_tasks = {
        blueprint["name"]: blueprint["status"]
        for blueprint in resp.json()["results"]
        if blueprint["status"] != "successful"
    }

    assert failed_tasks == {}


@pytest.mark.parametrize("privileged", [True, False])
def test_privileged_user_can_access_all_apps(
    hostvars: dict[str, Any], session: requests.Session, privileged: bool
) -> None:
    if privileged:
        token = hostvars["auth_authentik_superadmin_bootstrap_token"]
    else:
        resp = session.get(
            f"https://{hostvars['auth_authentik_hostname']}/api/v3/core/tokens/molecule-unprivileged-test-user-password/view_key/",
            headers={
                "Authorization": f"Bearer {hostvars['auth_authentik_superadmin_bootstrap_token']}"
            },
            allow_redirects=False,
            timeout=10,
        )

        assert resp.status_code == HTTPStatus.OK
        token = resp.json()["key"]

    resp = session.get(
        f"https://{hostvars['auth_authentik_hostname']}/api/v3/core/applications/",
        headers={"Authorization": f"Bearer {token}"},
        allow_redirects=False,
        timeout=10,
    )

    assert resp.status_code == HTTPStatus.OK
    print(yaml.dump(resp.json()))

    applications = sorted(r["slug"] for r in resp.json()["results"])

    if privileged or hostvars["default_monitor_agent_user_group"] is None:
        assert applications == [
            "benschubert-infrastructure-grafana",
            "benschubert-infrastructure-loki",
            "benschubert-infrastructure-mailpit",
            "benschubert-infrastructure-mimir",
            "benschubert-infrastructure-traefik-dashboard",
        ]
    else:
        assert applications == []
