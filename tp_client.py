import argparse
import socket
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")
    args = parser.parse_args()

    s = socket.create_connection((args.host, args.port))
    
    start_time = time.perf_counter()

    for _ in range(1000):
        s.sendall(b"ADD 1 2\n")
    
    responses_received = 0
    while responses_received < 1000:
        chunk = s.recv(4096)
        if not chunk:
            break
        responses_received += chunk.decode().count("\n")

    end_time = time.perf_counter()
    s.close()

    total_time = end_time - start_time
    ops_per_sec = 1000 / total_time

    print(f"Total Elapsed Time: {total_time:.4f} seconds")
    print(f"Throughput:         {ops_per_sec:.2f} operations/sec")
