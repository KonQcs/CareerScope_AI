import socket
from collections.abc import Generator
from typing import Any

import pytest

ALLOWED_NETWORK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    original_connect = socket.socket.connect

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        host = _host_from_address(address)
        if host in ALLOWED_NETWORK_HOSTS:
            return original_connect(self, address)
        raise RuntimeError(f"External network access is disabled during tests: {host}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    yield


def _host_from_address(address: Any) -> str:
    if isinstance(address, tuple) and address:
        return str(address[0])
    return str(address)
