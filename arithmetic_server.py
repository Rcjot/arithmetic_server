

### NOTE: Run this in the command-line as,
###
###     python3 socket_echo_server.py
###

import socket
import selectors
import types
import argparse

sel = selectors.DefaultSelector()


def arithmetic_unit(tokens) :
    tokenc = len(tokens)
    op = "" if tokenc <=0 else tokens[0]

    if (op == "ADD") :
        return "ADD"
    elif (op == "SUB") :
        return "SUB"
    elif (op == "MUL") :
        return "MUL"
    elif (op == "DIV") :
        return "DIV"
    elif (op == "RND") :
        return "RND"
    elif (op == "HIST") :
        return "HIST"
    elif (op == "HELP") :
        return """ 
    Commands:
    ADD <N1> <N2> Add N1 and N2.
    SUB <N1> <N2> Subtract N2 from N1.
    MUL <N1> <N2> Multiply N1 by N2.
    DIV <N1> <N2> Integer-divide N1 by N2.
    RND <N> Return a random integer in [1, N].
    HIST Show up to the last 5 valid operations for this connection only.
    HELP [command] Show all commands, or detailed help for one command.
    QUIT End the session.

    Server Responses:
    on success - OK <result>
    on any error - ERR <message>"""
    elif (op == "QUIT") :
        pass
    else: 
        return "ERR invalid command! Enter HELP to get help."
        

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
        except ConnectionResetError:
            # Catch the abrupt client hang-up safely!
            print(f"Client {data.addr} abruptly reset the connection.")
            sel.unregister(sock)
            sock.close()
            return
        if recv_data:
            if b'\xff\xf4' in recv_data:  # IAC IP
                print("IAC IP hello")
                data.outb = b""            # flush pending input
                
            if b'\xff\xfd\x06' in recv_data:  # IAC DO TIMING-MARK
                print("IAC DO TIMING MARK hello")
                sock.send(b'\xff\xfb\x06')    # reply IAC WILL TIMING-MARK → telnet resyncs
                return
            else :
                data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            # tokenize
            if b"\n" in data.outb :

                print("processing", data.outb)

                input_len = len(data.outb)

                # should ensure that the data.outb here can be decoded into utf-8
                clean_data = data.outb.decode("utf-8")

                commands = clean_data.split("\n")

                commands_tokens = tokenize_commands(commands)
                print("command_tokens", commands_tokens)
                commandc = len(commands_tokens)
                trailing = len(commands_tokens[commandc - 1])


                # effective length, jus  cuts off trailing unfinished command 
                eff_input_len = input_len - trailing

                print(eff_input_len)

                # do not include the last item
                # since it is either empty or incomplete
                for tokens in commands_tokens[:-1] :
                    if len(tokens) > 0 :
                        ret = arithmetic_unit(tokens) + "\n"
                        print("returned", ret)
                        sock.send(ret.encode("utf-8"))  # Should be ready to write
                print(data.outb, "before")
                data.outb = data.outb[eff_input_len:]# ...
                print(data.outb, "after")

            else : 
                if (len(data.outb) > 256) :
                    pass


                


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)



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




