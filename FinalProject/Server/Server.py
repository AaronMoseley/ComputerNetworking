from socket import socket, AF_INET, SOCK_STREAM
import string
from threading import Thread
from pathlib import Path
import os
import sys
import time

#Server Functions:
#   Receive request from client 1
#   Create thread that will handle client 1 request
#   Thread will check to see if file exists
#   If file doesn't exist, thread will request file from client 2 and wait to receive it
#   Thread will transmit file to client 1
#   Thread will wait for acknowledgement from client 1
#   Thread will end

def fileRequest(fileName: str, client1Sock: socket, client2Sock: socket)->bool:
    hadFile = True

    reqFile = Path(os.path.join(sys.path[0], fileName))
    if not reqFile.is_file():
        print(f"{fileName} not found")
        hadFile = False

        client2Sock.sendall(("REQ " + fileName).encode("utf-8"))

        file = open(os.path.join(sys.path[0], fileName), "wb")

        contents = client2Sock.recv(1024)
        file.write(contents)
        while sys.getsizeof(contents) >= 1024 and contents.decode("utf-8") != "EOF":
            print(contents.decode('utf-8'))
        
            contents = client2Sock.recv(1024)
            file.write(contents)

        file.close()

    else:
        print(f"{fileName} found")
        
    print("sending file")
    
    file = open(os.path.join(sys.path[0], fileName), "rb")
    contents = file.read(1024)
    while contents:
        client1Sock.sendall(contents)
        contents = file.read(1024)

    file.close()

    print("file sent")

    client1Sock.sendall(("EOF").encode('utf-8'))

    #resendTime = 15

    #startTime = time.perf_counter()
    response = client1Sock.recv(2048).decode('utf-8')
    print(response)
    while response.split()[0] != "ACK" or response.split()[1] != fileName:
        print(response)
        
        response = client1Sock.recv(2048).decode('utf-8')

    #if len(response.split()) > 2:
        #if "END" in response.split()[2]:
            #return True

    if not hadFile:
        os.remove(os.path.join(sys.path[0], fileName))

    return False

def main(host1name: str, port1no: int, host2name: str, port2no: int)->None:
    print(f"{host1name} {port1no} {host2name} {port2no}")

    server_sock1 = socket(AF_INET, SOCK_STREAM)
    server_sock1.bind((host1name, port1no))

    server_sock1.listen()

    client1Sock, client1Addr = server_sock1.accept()

    server_sock2 = socket(AF_INET, SOCK_STREAM)

    server_sock2.bind((host2name, port2no))

    server_sock2.listen()

    client2Sock, client2Addr = server_sock2.accept()

    request = client1Sock.recv(2048).decode('utf-8')

    while not "END" in request.split()[0]:
        print(request)
        if(request.split()[0] == "REQ"):
            print("test")
            if fileRequest(request.split()[1], client1Sock, client2Sock):
                print("ending")
                break

        try:
            request = client1Sock.recv(2048).decode('utf-8')
        except:
            request = "END"

        print(request)

    print(request)

    if client2Sock:
        client2Sock.send(("END").encode('utf-8'))
        client2Sock.close()

    client1Sock.close()

if __name__ == "__main__":
    main("localhost", 6060, "localhost", 8080)