from collections.abc import Iterator
from http import HTTPStatus
from typing import Any, TypedDict, cast

import pytest
import requests
from testinfra.host import Host

from . import LocalhostVerifyAdapter


class _TCache(TypedDict, total=False):
    authentik_credentials: tuple[str, str]
    hostvars: dict[str, Any]


@pytest.fixture(scope="session")
def cache() -> _TCache:
    return {}


@pytest.fixture(scope="module")
def hostvars(host: Host, cache: _TCache) -> dict[str, Any]:
    if "hostvars" not in cache:
        ret = host.ansible("debug", "var=hostvars[inventory_hostname]")
        cache["hostvars"] = ret["hostvars[inventory_hostname]"]

    return cache["hostvars"]


@pytest.fixture(scope="module")
def http_port(hostvars: dict[str, Any]) -> int:
    return cast(int, hostvars["ingress_http_port"])


@pytest.fixture(scope="module")
def https_port(hostvars: dict[str, Any]) -> int:
    return cast(int, hostvars["ingress_https_port"])


@pytest.fixture(scope="module")
def session(
    hostvars: dict[str, Any],
    https_port: int,
    cache: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[requests.Session]:
    if hostvars["ingress_custom_ca_cert_url"]:
        if "custom_ca_path" not in cache:
            resp = requests.get(
                hostvars["ingress_custom_ca_cert_url"],
                timeout=10,
            )
            resp.raise_for_status()

            path = tmp_path_factory.mktemp("cache").joinpath("custom_ca.pem")
            path.write_text(resp.text.strip())
            cache["custom_ca_path"] = str(path)

        verify = cache["custom_ca_path"]
    else:
        verify = hostvars["ingress_validate_certs"]

    with requests.Session() as session_:
        for hostname_var in [
            "auth_authentik_hostname",
            "ingress_traefik_dashboard_hostname",
            "monitoring_grafana_hostname",
            "monitoring_mimir_hostname",
        ]:
            hostname = hostvars[hostname_var]
            session_.mount(
                f"https://{hostname}",
                LocalhostVerifyAdapter(
                    "localhost",
                    https_port,
                    hostname,
                    verify,
                ),
            )

        yield session_


@pytest.fixture(scope="module")
def authentik_credentials(
    session: requests.Session, hostvars: dict[str, Any], cache: _TCache
) -> tuple[str, str]:
    if "authentik_credentials" not in cache:
        # Get akadmin user
        resp = session.get(
            f"https://{hostvars['auth_authentik_hostname']}/api/v3/core/tokens/molecule-test/view_key/",
            headers={
                "Authorization": f"Bearer {hostvars['auth_authentik_superadmin_bootstrap_token']}"
            },
            allow_redirects=False,
            timeout=10,
        )
        assert resp.status_code == HTTPStatus.OK
        cache["authentik_credentials"] = ("akadmin", resp.json()["key"])

    return cache["authentik_credentials"]
