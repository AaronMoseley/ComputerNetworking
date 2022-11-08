from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import sys
from pathlib import Path

def fileRequest(fileName: str, conn: socket)->None:
    reqFile = Path(os.path.join(sys.path[0], fileName))

    if reqFile.is_file():
        print(f"{fileName} is found")

        file = open(os.path.join(sys.path[0], fileName), "rb")
        contents = file.read(1024)
        while contents:
            conn.sendall(contents)
            contents = file.read(1024)

        file.close()

    conn.sendall(("EOF").encode('utf-8'))

def main(hostname: str, portno: int)->None:
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    request = conn.recv(2048).decode("utf-8")

    if sys.getsizeof(request) >= sys.getsizeof("END"):
        while request.split()[0] != "END" or sys.getsizeof(request) == 0:
            print(request)
            if(request.split()[0] == "REQ"):
                fileRequest(request.split()[1], conn)

            request = conn.recv(2048).decode("utf-8")

    conn.close()

if __name__ == "__main__":
    main("localhost", 8080)