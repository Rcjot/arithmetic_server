import socket
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")

    args = parser.parse_args()

    msg = "ADD 1 2\nSUB 3 4\nMUL 2 5\n"

    with socket.create_connection((args.host, args.port)) as s:
        s.sendall(msg.encode())
        expected = msg.count("\n")
        responses = b""
        while responses.count(b"\n") < expected:
            chunk = s.recv(4096)
            if not chunk:
                break
            responses += chunk
        print(responses.decode())
