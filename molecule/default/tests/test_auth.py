from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

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
        f"https://{hostvars['auth_authentik_hostname']}/api/v3/events/system_tasks/",
        headers={
            "Authorization": f"Bearer {hostvars['auth_authentik_superadmin_bootstrap_token']}"
        },
        allow_redirects=False,
        timeout=10,
    )

    assert resp.status_code == HTTPStatus.OK
    print(yaml.dump(resp.json()))

    failed_tasks = {
        task["full_name"]: {
            "description": task["description"],
            "status": task["status"],
        }
        for task in resp.json()["results"]
        if task["status"] != "successful"
        # Authentik has no network access to the outside
        and task["full_name"] != "update_latest_version"
    }

    assert failed_tasks == {}
