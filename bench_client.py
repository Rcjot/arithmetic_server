import argparse
import socket
import time
import statistics

def rtt_client(port, host):
    s = socket.create_connection((host, port))
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


def tp_client(port, host) :
    s = socket.create_connection((host, port))
    
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--mode", choices=["rtt", "tp"], required=True)

    args = parser.parse_args()

    if args.mode == "rtt":
        rtt_client(args.port, args.host)
    else:
        tp_client(args.port, args.host)


