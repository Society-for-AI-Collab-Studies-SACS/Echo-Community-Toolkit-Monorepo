import os
import json
import time

import pytest

import socket
from contextlib import closing


def _is_port_open(host: str, port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


@pytest.mark.skipif(
    os.environ.get("COLLAB_SMOKE_ENABLED") != "1",
    reason="Collab smoke disabled; set COLLAB_SMOKE_ENABLED=1 and run docker compose up -d",
)
def test_collab_health_endpoint():
    import http.client

    # Wait briefly for local compose or external service
    for _ in range(20):
        if _is_port_open("127.0.0.1", 8000):
            break
        time.sleep(0.25)

    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=3)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    assert resp.status == 200
    data = json.loads(resp.read().decode("utf-8"))
    assert data.get("status") == "ok"

