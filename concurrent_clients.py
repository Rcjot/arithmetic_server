import argparse
import socket
import statistics
import time
from concurrent.futures import ProcessPoolExecutor


def run_single_client(host, port):
    """Simulates one instance of the M1 sequential client."""
    try:
        s = socket.create_connection((host, port))
        msg = b"ADD 1 2\n"
        rtts = []
        for _ in range(1000):
            start = time.perf_counter()
            s.sendall(msg)
            s.recv(1024)
            rtts.append((time.perf_counter() - start) * 1000)
        s.close()
        return statistics.mean(rtts)
    except Exception as e:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")
    args = parser.parse_args()

    for concurrency in [5, 10, 20]:
        print(f"Spawning {concurrency} concurrent clients...")

        with ProcessPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(run_single_client, args.host, args.port)
                for _ in range(concurrency)
            ]
            results = [f.result() for f in futures if f.result() is not None]

        if results:
            overall_mean = statistics.mean(results)
            print(f"--> Concurrency {concurrency} | Overall Mean RTT: {overall_mean:.3f} ms\n")
