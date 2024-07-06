import json
from collections import defaultdict
from typing import cast

import pytest
from testinfra.host import Host


@pytest.fixture(scope="module")
def containers(host: Host) -> list[str]:
    result = host.run("podman ps --all --format '{{ '{{' }}.Names{{ '}}' }}'")
    assert result.succeeded

    return cast(list[str], result.stdout.split())


@pytest.fixture(scope="module")
def pods(host: Host) -> list[str]:
    result = host.run("podman pod ps --format '{{ '{{' }}.Name{{ '}}' }}'")
    assert result.succeeded

    return cast(list[str], result.stdout.split())


def test_no_volumes_are_created(host: Host, containers: list[str]) -> None:
    result = host.run(f"podman inspect {' '.join(containers)}")
    assert result.succeeded

    container_infos = json.loads(result.stdout)

    volumes_mounted = defaultdict(list)

    for container_name, container_info in zip(
        containers,
        container_infos,
        strict=True,
    ):
        for mount in container_info["Mounts"]:
            if mount["Type"] == "volume":
                volumes_mounted[container_name].append(mount["Destination"])

    assert not dict(
        volumes_mounted,
    ), "Some containers have volumes that are not attached"


def test_all_containers_succeed_healthchecks(
    host: Host,
    containers: list[str],
) -> None:
    errors = {}

    for container in containers:
        if container.endswith("-infra"):
            continue  # infra containers don't have healthchecks

        res = host.run(f"podman healthcheck run {container}")
        if container == "monitoring-mimir-mimir":
            assert res.exit_status != 0, "Mimir did not have healthchecks set?"
        elif res.exit_status != 0:
            errors[container] = res.stderr

    assert not errors, "Some containers failed their healtchecks"


def test_all_pods_run_in_a_user_namespace(host: Host, pods: list[str]) -> None:
    result = host.run(f"podman inspect {' '.join(pods)}")
    assert result.succeeded

    assert not [
        pod
        for pod, info in zip(pods, json.loads(result.stdout), strict=True)
        if "user" not in info["SharedNamespaces"]
    ]


def test_all_networks_are_internal(host: Host) -> None:
    result = host.run("podman network ls --quiet")
    assert result.succeeded

    result = host.run(
        f"podman network inspect {' '.join(result.stdout.splitlines())}",
    )
    assert result.succeeded

    networks = json.loads(result.stdout)
    networks_without_internal = [
        network["name"] for network in networks if not network["internal"]
    ]
    assert networks_without_internal == [
        # traefik needs outside world access to generate ssl certificates
        "ingress",
        # The default podman network
        "podman",
    ]
