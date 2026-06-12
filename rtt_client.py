import argparse
import socket
import statistics
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")
    args = parser.parse_args()

    s = socket.create_connection((args.host, args.port))
    msg = b"ADD 1 2\n"
    rtts = []

    for _ in range(1000):
        start_time = time.perf_counter()  

        s.sendall(msg)
        s.recv(1024)

        end_time = time.perf_counter()
        rtts.append((end_time - start_time) * 1000)

    s.close()

    print(f"Mean RTT:   {statistics.mean(rtts):.3f} ms")
    print(f"Median RTT: {statistics.median(rtts):.3f} ms")
