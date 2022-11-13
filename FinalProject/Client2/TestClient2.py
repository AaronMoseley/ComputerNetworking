from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import sys
from pathlib import Path

def fileRequest(fileName: str, conn: socket)->None:
    reqFile = Path(os.path.join(sys.path[0], fileName))

    if reqFile.is_file():
        print(f"Sending {fileName}")

        file = open(os.path.join(sys.path[0], fileName), "rb")
        contents = file.read(1024)
        while contents:
            conn.sendall(contents)
            contents = file.read(1024)

        file.close()

    print(f"{fileName} sent")

def main(hostname: str, portno: int)->None:
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    print("Connected to server")

    request = conn.recv(2048).decode("utf-8")

    if sys.getsizeof(request) >= sys.getsizeof("END"):
        while request.split()[0] != "END" or sys.getsizeof(request) == 0:
            if(request.split()[0] == "REQ"):
                print(f"{request.split()[1]} requested")
                fileRequest(request.split()[1], conn)

            request = conn.recv(2048).decode("utf-8")

    conn.close()

    print("Exiting")

if __name__ == "__main__":
    ip = input("Please input the IPv4 address of the host: ")
    port = int(input("Please input the port to connect: "))

    main(ip, port)