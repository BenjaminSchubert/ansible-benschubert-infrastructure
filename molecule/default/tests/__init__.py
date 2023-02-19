from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import urlparse

import requests
import requests.adapters
import urllib3.connectionpool
import yaml


def str_presenter(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Represent data nicely when it's multiline"""
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar(
            "tag:yaml.org,2002:str",
            data,
            style="|",
        )
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)


class LocalhostVerifyAdapter(requests.adapters.HTTPAdapter):
    def __init__(
        self,
        real_target: str,
        port: str,
        server_hostname: str,
        verify: bool | str,
    ) -> None:
        self._real_target = real_target
        self._port = port
        self._server_hostname = server_hostname
        self._verify = verify
        super().__init__()

    def add_headers(self, request: requests.Request, **kwargs: Any) -> None:
        assert "HOST" not in request.headers
        request.headers["HOST"] = urlparse(request.url).hostname
        super().add_headers(request, **kwargs)  # type: ignore[no-untyped-call]

    def get_connection(
        self,
        url: str,
        proxies: dict[str, str] | None = None,
    ) -> urllib3.connectionpool.ConnectionPool:
        scheme = urlparse(url).scheme
        return cast(
            urllib3.connectionpool.ConnectionPool,
            super().get_connection(  # type: ignore[no-untyped-call]
                f"{scheme}://{self._real_target}:{self._port}",
                proxies,
            ),
        )

    def send(
        self,
        request: requests.PreparedRequest,
        stream: bool = False,
        timeout: None
        | float
        | tuple[float, float]
        | tuple[float, None] = None,
        verify: bool | str = True,  # noqa: ARG002
        cert: bytes | str | tuple[bytes | str, bytes | str] | None = None,
        proxies: Mapping[str, str] | None = None,
    ) -> requests.Response:
        return super().send(
            request,
            stream,
            timeout,
            self._verify,
            cert,
            proxies,
        )

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = requests.adapters.DEFAULT_POOLBLOCK,
        **pool_kwargs: Any,
    ) -> None:
        pool_kwargs["server_hostname"] = self._server_hostname
        super().init_poolmanager(  # type: ignore[no-untyped-call]
            connections,
            maxsize,
            block,
            **pool_kwargs,
        )
