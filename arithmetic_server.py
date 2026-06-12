### NOTE: Run this in the command-line as,
###
###     python3 socket_echo_server.py
###

import socket
import selectors
import types
import argparse
import random
from datetime import datetime

sel = selectors.DefaultSelector()


def arithmetic_unit(tokens, hist, writing_idx) :
    """
    returns 
        response, ok

    response -  response from opes or message when error
    ok - True or False
    """

    two_params = ["ADD", "SUB", "MUL", "DIV"]
    res = ""
    ok = True
    quitting = False
    hist_append = False

    tokenc = len(tokens)
    op = "" if tokenc <=0 else tokens[0]

    if op in two_params :
        if tokenc != 3 :
            return f"Invalid number of arguments to {op}", False, quitting, hist_append

        try :
            operand1 = int(tokens[1])
            operand2 = int(tokens[2])
        except :
            return "One of the operands is an invalid integer", False, quitting, hist_append


        if (op == "ADD") :
            res = operand1 + operand2 
        elif (op == "SUB") :
            res = operand1 - operand2 
        elif (op == "MUL") :
            res = operand1 * operand2 
        elif (op == "DIV") :
            if operand2 == 0 :
                return "Divisor cannot be zero", False, quitting, hist_append
            res = operand1 / operand2 

        hist_append = True
    elif (op == "RND") :
        if tokenc != 2 :
            return f"Invalid number of arguments to RND", False, quitting, hist_append

        try :
            operand1 = int(tokens[1])
        except :
            return "One of the operands is an invalid integer", False, quitting, hist_append

        res = random.randint(1, operand1)

        hist_append = True
    elif (op == "HIST") :
        newest_chunk = "\n".join(hist[:writing_idx:])

        oldest_chunk = "\n".join(hist[writing_idx::]) if None not in hist else ""

        res = "The last valid operations from this session (up to 5) are:\n"

        if oldest_chunk :
            res += oldest_chunk + "\n" + newest_chunk
        else :
            res += newest_chunk
    elif (op == "HELP") :
        valid_args = ["GLOBAL", "ADD", "SUB", "MUL", "DIV", "RND", "HIST", "HELP", "QUIT"]

        if tokenc > 2 :
            return f"Invalid number of arguments to HELP", False, quitting, hist_append
        arg = tokens[1] if tokenc == 2 else "GLOBAL"

        if arg not in valid_args :
            return f"Such operation does not exist!", False, quitting, hist_append

        help_map = {
            "GLOBAL": """The following commands are available:
ADD <N1> <N2>   - to add N1 and N2
SUB <N1> <N2>   - to subtract N2 from N1
MUL <N1> <N2>   - to multiply N1 by N2
DIV <N1> <N2>   - to divide N1 by N2
RND <N>         - to generate a random number between 1 and N, inclusive
HIST            - to show the last 5 valid operations in the session
HELP [command]  - to display the syntax and semantics of a specific
command. If no command is specified, it will display all the available
commands and their meanings
QUIT            - to end the current session of the arithmetic server""",

            "ADD": "ADD <N1> <N2> - to add N1 and N2",
            "SUB": "SUB <N1> <N2> - to subtract N2 from N1",
            "MUL": "MUL <N1> <N2> - to multiply N1 by N2",
            "DIV": "DIV <N1> <N2> - to divide N1 by N2",
            "RND": "RND <N> - to generate a random number between 1 and N, inclusive",
            "HIST": "HIST - to show the last 5 valid operations in the session",
            "HELP": """HELP [command] - to display the syntax and semantics of a specific
command. If no command is specified, it will display all the available
commands and their meanings""",
            "QUIT": "QUIT - to end the current session of the arithmetic server"
        }  
        res = help_map[arg] + "\n"

    elif (op == "QUIT") :
        res = "Bye."
        quitting = True
    else: 
        res =  f"Unknown operation {op}"
        ok = False
    
    return str(res), ok, quitting, hist_append
        

def tokenize_commands(commands) :
    commands_tokens = []
    for command in commands :
        commands_tokens.append(command.split())

    return commands_tokens


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
            
            # Timestamp generation (millisecond precision: HH:MM:SS.mmm)
            now = datetime.now()
            timestamp = now.strftime("[%H:%M:%S") + f".{now.microsecond // 1000:03d}]"
            
            # Client information context
            client_ip, client_port = data.addr
            
            # Construct the exact log layout required
            log_line = f"{timestamp} {client_ip}:{client_port} recv() -> {len(recv_data)} bytes {repr(recv_data)}\n"
            
            # Append log transaction securely to file
            with open("recv.log", "a", encoding="utf-8") as log_file:
                log_file.write(log_line)

        except ConnectionResetError:
            # Catch the abrupt client hang-up safely
            print(f"Client {data.addr} abruptly reset the connection.")
            sel.unregister(sock)
            sock.close()
            return
        if recv_data:
            is_iac_ip = b'\xff\xf4' in recv_data
            is_timing_mark = b'\xff\xfd\x06' in recv_data

            if is_iac_ip:
                data.inb = b""

            if is_timing_mark:
                sock.send(b'\xff\xfb\x06')
                return

            if not is_iac_ip and not is_timing_mark:
                data.inb += recv_data

            # process any complete commands immediately
            if b"\n" in data.inb:
                clean_data = data.inb.decode("utf-8")
                commands = clean_data.split("\n")
                print("commands", commands)

                commands_tokens = tokenize_commands(commands)

                commandc = len(commands_tokens)
                trailing = len(commands_tokens[commandc - 1])
                input_len = len(data.inb)
                eff_input_len = input_len - trailing

                for index, tokens in enumerate(commands_tokens[:-1]):
                    if len(tokens) > 0:

                        command_len = len(commands[index]) + 1
                        if command_len > 256:
                            data.outb += b"ERR command too long\n"
                            continue

                        ret, ok, quitting, hist_append = arithmetic_unit(tokens, data.hist, data.writing_idx)

                        if hist_append:
                            data.hist[data.writing_idx] = " ".join(tokens) + f" -> {ret}"
                            data.writing_idx = (data.writing_idx + 1) % 5

                        if ok:
                            ret = "OK " + ret
                        else:
                            ret = "ERR " + ret

                        ret += "\n"
                        data.outb += ret.encode("utf-8")

                        if quitting:
                            data.closing = True
                            break

                print(data.inb, "before")
                data.inb = data.inb[eff_input_len:]
                print(data.inb, "after")

        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
        if data.closing and not data.outb:
            print(f"Closing connection to {data.addr} after QUIT")
            sel.unregister(sock)
            sock.close()


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", closing=False, hist=[None] * 5, writing_idx=0)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

    welcome_msg = "OK Welcome to the CSc 113 Arithmetic Server!\n"
    conn.sendall(welcome_msg.encode("utf-8"))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14344)
    parser.add_argument("--host", type=str, default="localhost")

    args = parser.parse_args()

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = ('127.0.0.1', args.port)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    sock.setblocking(False)

    sel.register(sock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()
