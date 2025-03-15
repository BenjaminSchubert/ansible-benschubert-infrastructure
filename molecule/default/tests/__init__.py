from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import ParseResult, urlparse

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
        port: int,
        server_hostname: str,
        verify: bool | str,
    ) -> None:
        self._real_target = real_target
        self._port = port
        self._server_hostname = server_hostname
        self._verify = verify
        super().__init__()

    def get_connection_with_tls_context(
        self,
        request: requests.PreparedRequest,
        verify: bool | str | None,
        proxies: Mapping[str, str] | None = None,
        cert: tuple[str, str] | str | None = None,
    ) -> urllib3.connectionpool.ConnectionPool:
        url = cast("ParseResult", urlparse(request.url))
        assert url.hostname is not None

        if self._port == 443:  # noqa: PLR2004
            request.headers["HOST"] = url.hostname
        else:
            request.headers["HOST"] = f"{url.hostname}:{self._port}"

        request.url = url._replace(
            netloc=f"{self._real_target}:{self._port}"
        ).geturl()

        return super().get_connection_with_tls_context(
            request, verify, proxies, cert
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
