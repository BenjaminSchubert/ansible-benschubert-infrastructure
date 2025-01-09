import json
from collections import defaultdict
from typing import cast

import pytest
from testinfra.host import Host


@pytest.fixture(scope="module")
def containers(host: Host) -> list[str]:
    result = host.run(
        "podman container ps --all --format '{{ '{{' }}.Names{{ '}}' }}'"
    )
    assert result.succeeded

    return cast(list[str], result.stdout.split())


@pytest.fixture(scope="module")
def pods(host: Host) -> list[str]:
    result = host.run("podman pod ps --format '{{ '{{' }}.Name{{ '}}' }}'")
    assert result.succeeded

    return cast(list[str], result.stdout.split())


def test_no_volumes_are_created(host: Host, containers: list[str]) -> None:
    mount_format = "{{ '{{' }} json .Mounts {{ '}}' }}"
    result = host.run(
        f"podman inspect --format '{mount_format}' {' '.join(containers)}",
    )
    assert result.succeeded

    containers_mounts = [
        json.loads(line) for line in result.stdout.strip().splitlines()
    ]

    volumes_mounted = defaultdict(list)

    for container_name, mounts in zip(
        containers,
        containers_mounts,
        strict=True,
    ):
        for mount in mounts:
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
    result = host.run(f"podman pod inspect {' '.join(pods)}")
    assert result.succeeded

    assert [
        pod
        for pod, info in zip(pods, json.loads(result.stdout), strict=True)
        if "user" not in info["SharedNamespaces"]
    ] == [], "Some pods are not running in a user namespace"


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


def test_all_containers_have_a_read_only_rootfs(
    host: Host, containers: list[str]
) -> None:
    readonly_format = "{{ '{{' }} .HostConfig.ReadonlyRootfs {{ '}}' }}"
    result = host.run(
        f"podman inspect --format '{readonly_format}' {' '.join(containers)}"
    )
    assert result.succeeded

    assert [
        container
        for container, readonly in zip(
            containers,
            result.stdout.strip().splitlines(),
            strict=True,
        )
        # FIXME: can we make the infra containers readonly?
        if not container.endswith("-infra") and not json.loads(readonly)
    ] == [], "Some containers are not setup as readonly"


def test_all_containers_have_minimal_capabilities(
    host: Host, containers: list[str]
) -> None:
    caps_format = "{{ '{{' }} json .BoundingCaps {{ '}}' }}"
    result = host.run(
        f"podman inspect --format '{caps_format}' {' '.join(containers)}"
    )
    assert result.succeeded
    all_caps = (
        json.loads(caps) for caps in result.stdout.strip().splitlines()
    )

    assert {
        container: caps
        for container, caps in zip(containers, all_caps, strict=True)
        if not container.endswith("-infra") and caps
    } == {
        "ingress-traefik": ["CAP_NET_BIND_SERVICE"],
    } | {
        f"{group}-monitor-agent": ["CAP_DAC_OVERRIDE"]
        for group in ["auth", "ingress", "monitoring"]
    }, "Some containers have too many capabiliti4es"
