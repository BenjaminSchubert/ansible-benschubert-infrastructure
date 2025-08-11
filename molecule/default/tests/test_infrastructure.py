import json
import time
from collections import defaultdict
from multiprocessing.pool import ThreadPool
from typing import cast

import pytest
from testinfra.host import Host


@pytest.fixture(scope="module")
def containers(host: Host) -> list[str]:
    result = host.run(
        "podman container ps --all --format '{{ '{{' }}.Names{{ '}}' }}'"
    )
    assert result.succeeded

    return cast("list[str]", sorted(result.stdout.split()))


@pytest.mark.xdist_group(name="containers")
def test_infrastructure_service_starts_and_stops_all_services(
    host: Host, containers: list[str]
) -> None:
    # 1. Stop the service
    result = host.run(
        "XDG_RUNTIME_DIR=/run/user/1000 systemctl --user stop infrastructure.target"
    )
    assert result.succeeded

    # 2. No more containers running
    for _ in range(30):
        try:
            result = host.run(
                "podman container ps --all --format '{{ '{{' }}.Names{{ '}}' }}'"
            )
            assert result.succeeded
            assert result.stdout.split() == [], (
                "Some containers are still running"
            )
            break
        except AssertionError as exc:
            e = exc
            time.sleep(1)
    else:
        raise e  # pylint: disable=used-before-assignment

    # 3. Restarting the service
    result = host.run(
        "XDG_RUNTIME_DIR=/run/user/1000 systemctl --user start infrastructure.target"
    )
    assert result.succeeded

    # 4. We get the same amount of containers as at the start
    result = host.run(
        "podman container ps --all --format '{{ '{{' }}.Names{{ '}}' }}'"
    )
    assert result.succeeded
    assert sorted(result.stdout.split()) == containers


@pytest.mark.xdist_group(name="containers")
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


@pytest.mark.xdist_group(name="containers")
def test_all_containers_succeed_healthchecks(
    host: Host,
    containers: list[str],
) -> None:
    errors = {}
    containers = [c for c in containers if not c.endswith("-infra")]

    with ThreadPool(len(containers)) as pool:
        for container, res in zip(
            containers,
            pool.map(
                lambda c: host.run(f"podman healthcheck run {c}"), containers
            ),
            strict=True,
        ):
            if container == "monitoring-mimir":
                assert res.exit_status != 0, (
                    "Mimir did not have healthchecks set?"
                )
            elif res.exit_status != 0:
                errors[container] = res.stderr

    assert not errors, "Some containers failed their healtchecks"


def test_all_containers_run_in_a_user_namespace(
    host: Host, containers: list[str]
) -> None:
    result = host.run(f"podman inspect {' '.join(containers)}")
    assert result.succeeded

    assert [
        container
        for container, info in zip(
            containers, json.loads(result.stdout), strict=True
        )
        if info["HostConfig"]["UsernsMode"] != "private"
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
    assert sorted(networks_without_internal) == [
        # traefik needs outside world access to generate ssl certificates
        "ingress",
        # Grafana also requires internet access for plugins
        "monitoring-grafana-external",
        # The default podman network
        "podman",
    ]


@pytest.mark.xdist_group(name="containers")
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
        if not json.loads(readonly)
    ] == [], "Some containers are not setup as readonly"


@pytest.mark.xdist_group(name="containers")
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
        "ingress": ["CAP_NET_BIND_SERVICE"],
    } | {
        f"{group}-monitoring": ["CAP_DAC_OVERRIDE"]
        for group in ["auth", "ingress", "monitoring"]
    }, "Some containers have too many capabiliti4es"
