import re
from collections import defaultdict
from http import HTTPStatus
from typing import cast

import pytest
from testinfra.host import Host

LINE_RE = re.compile(
    r'"CONNECT (?P<host>[^:"\s]+):(?P<port>\d+)"\s+'
    r"response_code=(?P<code>\d+)\s+flags=(?P<flags>\S+)"
)


@pytest.fixture(scope="module")
def containers(host: Host) -> list[str]:
    result = host.run(
        "sudo podman container ps --all --filter 'name=-egress' --format '{{ .Names }}'"
    )
    assert result.succeeded

    return cast("list[str]", sorted(result.stdout.split()))


def test_no_remote_calls_were_blocked(
    host: Host, containers: list[str]
) -> None:
    failures = defaultdict(set)

    for container in containers:
        result = host.run(f"sudo podman logs {container}")
        assert result.succeeded

        for hostname, _port, code, _flags in LINE_RE.findall(result.stdout):
            if int(code) != HTTPStatus.OK:
                failures[container].add((hostname, int(code)))

    assert failures == {}
