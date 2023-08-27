import os
from collections.abc import Iterator
from typing import Any, cast

import pytest
import requests
from testinfra.host import Host

from . import LocalhostVerifyAdapter


@pytest.fixture(scope="session")
def cache() -> dict[str, Any]:
    return {}


@pytest.fixture(scope="module")
def hostvars(host: Host, cache: dict[str, Any]) -> dict[str, Any]:
    if "hostvars" not in cache:
        ret = host.ansible("debug", "var=hostvars[inventory_hostname]")
        cache["hostvars"] = ret["hostvars[inventory_hostname]"]

    return cast(dict[str, Any], cache["hostvars"])


@pytest.fixture(scope="session")
def exposed_http_port() -> str:
    return os.environ.get("HTTP_PORT", "16080")


@pytest.fixture(scope="session")
def exposed_https_port() -> str:
    return os.environ.get("HTTPS_PORT", "16443")


@pytest.fixture(scope="module")
def session(
    hostvars: dict[str, Any],
    exposed_https_port: str,
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
                    exposed_https_port,
                    hostname,
                    verify,
                ),
            )

        yield session_
