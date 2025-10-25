"""Quick smoke test for the collaboration scaffolding."""

from library_core.collab.client import CollaborationClient
from library_core.collab.server import CollaborationServer


def main() -> None:
    server = CollaborationServer()
    client = CollaborationClient()
    client.connect("ws://localhost:8080", "demo-session", "tester")
    server.record("presence", "tester", {"action": "join"})
    print("History length:", len(tuple(server.history)))


if __name__ == "__main__":
    main()
