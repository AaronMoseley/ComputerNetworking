import socket
from socket import socket, AF_INET, SOCK_STREAM
import string
from threading import Thread
from pathlib import Path
import os
import sys
import time

def fileRequest(fileName: str, client1Sock: socket, client2Sock: socket)->None:
    hadFile = True

    reqFile = Path(os.path.join(sys.path[0], fileName))
    if not reqFile.is_file():
        print(f"{fileName} not found, requesting from Client 2")
        hadFile = False

        client2Sock.sendall(("REQ " + fileName).encode("utf-8"))

        file = open(os.path.join(sys.path[0], fileName), "wb")

        contents = client2Sock.recv(1024)
        file.write(contents)
        while sys.getsizeof(contents) >= 1024:
            contents = client2Sock.recv(1024)
            file.write(contents)

        file.close()

        print(f"{fileName} downloaded from Client 2")

    else:
        print(f"{fileName} found")
        
    print(f"Sending file {fileName} to Client 1")
    
    file = open(os.path.join(sys.path[0], fileName), "rb")
    contents = file.read(1024)
    while contents:
        client1Sock.sendall(contents)
        contents = file.read(1024)

    file.close()

    print(f"{fileName} sent to Client 1")

    response = client1Sock.recv(2048).decode('utf-8')
    while response.split()[0] != "ACK" or response.split()[1] != fileName:
        response = client1Sock.recv(2048).decode('utf-8')

    print(f"{fileName} acknowledged from Client 1")

    if not hadFile:
        os.remove(os.path.join(sys.path[0], fileName))

def main(host1name: str, port1no: int, host2name: str, port2no: int)->None:
    print("Waiting for connections")

    server_sock1 = socket(AF_INET, SOCK_STREAM)
    server_sock1.bind((host1name, port1no))
    server_sock1.listen()

    client1Sock, client1Addr = server_sock1.accept()

    print("Client 1 connected")

    server_sock2 = socket(AF_INET, SOCK_STREAM)
    server_sock2.bind((host2name, port2no))
    server_sock2.listen()

    client2Sock, client2Addr = server_sock2.accept()

    print("Client 2 connected")

    request = client1Sock.recv(2048).decode('utf-8')

    while not "END" in request.split()[0]:
        if(request.split()[0] == "REQ"):
            print(f"Requested File {request.split()[1]}")
            fileRequest(request.split()[1], client1Sock, client2Sock)

        try:
            request = client1Sock.recv(2048).decode('utf-8')
        except:
            request = "END"

    if client2Sock:
        client2Sock.send(("END").encode('utf-8'))
        client2Sock.close()

    client1Sock.close()

    print("Exiting")

if __name__ == "__main__":
    port1 = int(input("Please input the first client's port: "))
    port2 = int(input("Please input the second client's port: "))

    #Current Local IP: 192.168.1.39

    ip = input("Please input the local IPv4 address: ")

    main(ip, port1, ip, port2)