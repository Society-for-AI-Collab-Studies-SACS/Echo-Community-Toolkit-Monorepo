import socket
import sys
import time


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("", 5550))
        server_sock.listen(5)
        server_sock.settimeout(1.0)
        print("Message broker stub listening on port 5550", flush=True)

        while True:
            try:
                connection, _ = server_sock.accept()
            except socket.timeout:
                continue
            except Exception as exc:
                print(f"Listener error: {exc}", file=sys.stderr, flush=True)
                time.sleep(0.5)
                continue
            try:
                connection.settimeout(0.5)
                while True:
                    data = connection.recv(1024)
                    if not data:
                        break
            except (socket.timeout, ConnectionResetError):
                pass
            finally:
                connection.close()


if __name__ == "__main__":
    main()
