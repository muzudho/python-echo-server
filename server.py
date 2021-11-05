import socket
from threading import Thread
import sys
import signal

MESSAGE_SIZE = 1024

server_sock = None
separator_token = "<SEP>"  # we will use this to separate the client name & message
client_sockets = None


def sigterm_handler(_signum, _frame) -> None:
    sys.exit(1)


def clean_up():
    global server_sock
    global client_sockets

    # close client sockets
    print("Clean up")
    if not (client_sockets is None):
        for cs in client_sockets:
            cs.close()

    # close server socket
    if not (server_sock is None):
        server_sock.close()


def listen_for_client(client_sock):
    """
    This function keep listening for a message from `client_sock` socket
    Whenever a message is received, broadcast it to all other connected clients
    """
    global separator_token
    global client_sockets

    while True:
        try:
            # keep listening for a message from `client_sock` socket
            msg = client_sock.recv(MESSAGE_SIZE).decode()
        except Exception as e:
            # client no longer connected
            # remove it from the set
            print(f"[!] Error: {e}")

            print(f"Remove a socket")
            client_sockets.remove(client_sock)
            break

        # とりあえずエコー
        msg = f"Echo: {msg}"
        client_sock.send(msg.encode())


def run_server():
    global server_sock
    global client_sockets

    # server's IP address
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5002  # port we want to use

    # initialize list/set of all connected client's sockets
    client_sockets = set()

    # create a TCP socket
    server_sock = socket.socket()

    # make the port as reusable port
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind the socket to the address we specified
    server_sock.bind((SERVER_HOST, SERVER_PORT))

    # listen for upcoming connections
    server_sock.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    while True:
        print(f"Wait a connection")
        # we keep listening for new connections all the time
        client_socket, client_address = server_sock.accept()
        print(f"[+] {client_address} connected.")

        # add the new connected client to connected sockets
        client_sockets.add(client_socket)

        # start a new thread that listens for each client's messages
        thr = Thread(target=listen_for_client, args=(client_socket,))

        # make the thread daemon so it ends whenever the main thread ends
        thr.daemon = True

        # start the thread
        thr.start()


def main():
    # 強制終了のシグナルを受け取ったら、強制終了するようにします
    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        run_server()
    finally:
        # 強制終了のシグナルを無視するようにしてから、クリーンアップ処理へ進みます
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        clean_up()
        # 強制終了のシグナルを有効に戻します
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)


# このファイルを直接実行したときは、以下の関数を呼び出します
if __name__ == "__main__":
    sys.exit(main())
