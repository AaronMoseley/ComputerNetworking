from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from pathlib import Path
import os
import sys

def main(hostname: str, portno: int)->None:
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    print("Connected to server")

    fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")

    while fileName.lower() != "quit":
        message = "REQ " + fileName
        conn.sendall(message.encode('utf-8'))

        if Path(os.path.join(sys.path[0], fileName)).is_file():
            print(f"{fileName} already exists")
            fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")
            continue

        print(f"Requested {fileName}")

        f = open(os.path.join(sys.path[0], fileName), "wb")

        contents = conn.recv(1024)
        f.write(contents)

        while sys.getsizeof(contents) >= 1024:
            contents = conn.recv(1024)
            f.write(contents)

        f.close()

        print(f"Received {fileName}")

        conn.sendall(("ACK " + fileName).encode('utf-8'))

        print(f"Acknowledged {fileName}")

        fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")

    message = "END"
    conn.sendall(message.encode('utf-8'))

    conn.close()

    print("Exiting")

if __name__ == "__main__":
    ip = input("Please input the IP address of the server: ")
    port = int(input("Please input the port to connect: "))

    main(ip, port)