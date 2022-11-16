import socket
from socket import socket, AF_INET, SOCK_STREAM
import string
from threading import Thread
from pathlib import Path
import os
import sys
import time

def fileRequest(fileName: str, client1Sock: socket, client2Sock: socket)->None:
    #Checks if the file exists on the server, requests from client 2 if it doesn't
    hadFile = True
    reqFile = Path(os.path.join(sys.path[0], fileName))

    if not reqFile.is_file():
        print(f"{fileName} not found, requesting from Client 2")
        hadFile = False

        #Sends request (REQ fileName) to client 2
        client2Sock.sendall(("REQ " + fileName).encode("utf-8"))

        #Receives 1024 of the file from client 2
        contents = bytearray(client2Sock.recv(1024))

        #Decodes 3-character tail from end of message
        #Tail is either EOF (end of file) or NEF (not end file)
        tail = contents[-3:]
        tailStr = tail.decode('utf-8')

        #Checks if the file was found in client 2
        if tailStr == "ERR":
            print("File not found, sending error")
            message = "File not found"
            client1Sock.sendall((message + "ERR").encode('utf-8'))
            return

        #Removes tail from contents and writes to file
        contents = contents[: len(contents) - 3]

        file = open(os.path.join(sys.path[0], fileName), "wb")
        file.write(contents)

        #Loops until the tail is EOF, repeats same code as above
        while tailStr != "EOF":
            contents = bytearray(client2Sock.recv(1024))

            tail = contents[-3:]
            tailStr = tail.decode('utf-8')

            contents = contents[: len(contents) - 3]
            file.write(contents)

        file.close()

        print(f"{fileName} downloaded from Client 2")

    else:
        print(f"{fileName} found")
        
    #Begins to send file to client 1
    print(f"Sending file {fileName} to Client 1")
    
    file = open(os.path.join(sys.path[0], fileName), "rb")

    #Logs size of file and starts a counter
    fileSize = os.path.getsize(os.path.join(sys.path[0], fileName))
    currPos = 0

    #Reads 1021 bytes from file, increments counter, appends NEF or EOF to contents depending on whether the end of file has been reached
    contents = bytearray(file.read(1021))
    currPos += len(contents)

    if currPos < fileSize:
        contents.extend("NEF".encode('utf-8'))
    else:
        contents.extend("EOF".encode('utf-8'))

    #Sends full message to client 1
    client1Sock.sendall(contents)

    #Loop until counter reaches the total file size, repeat same code as above
    while currPos < fileSize:
        contents = bytearray(file.read(1021))
        currPos += len(contents)

        if currPos < fileSize:
            contents.extend("NEF".encode('utf-8'))
        else:
            contents.extend("EOF".encode('utf-8'))

        client1Sock.sendall(contents)

    file.close()

    print(f"{fileName} sent to Client 1")

    #Receives acknowledgement from client 1 (ACK fileName)
    response = client1Sock.recv(2048).decode('utf-8')
    while response.split()[0] != "ACK" or response.split()[1] != fileName:
        response = client1Sock.recv(2048).decode('utf-8')

    print(f"{fileName} acknowledged from Client 1")

    #If file wasn't originally on server, deletes it
    if not hadFile:
        os.remove(os.path.join(sys.path[0], fileName))

def main(host1name: str, port1no: int, host2name: str, port2no: int)->None:
    print("Waiting for connections")

    #Connects to client 1
    server_sock1 = socket(AF_INET, SOCK_STREAM)
    server_sock1.bind((host1name, port1no))
    server_sock1.listen()

    client1Sock, client1Addr = server_sock1.accept()

    print("Client 1 connected")

    #Connects to client 2
    server_sock2 = socket(AF_INET, SOCK_STREAM)
    server_sock2.bind((host2name, port2no))
    server_sock2.listen()

    client2Sock, client2Addr = server_sock2.accept()

    print("Client 2 connected")

    #Receives first request from client 1
    request = client1Sock.recv(2048).decode('utf-8')

    #Loops until client 1 cancels program
    while not "END" in request.split()[0]:
        #Calls file request function if a request has been issued
        #Request Format: REQ fileName
        if(request.split()[0] == "REQ"):
            print(f"Requested File {request.split()[1]}")
            fileRequest(request.split()[1], client1Sock, client2Sock)

        #Takes in next request, if invalid assumes that the connection has been cancelled
        try:
            request = client1Sock.recv(2048).decode('utf-8')
        except:
            request = "END"

    #If the client 2 connection is still valid, indicate to it that the connection is over and closes the connections
    if client2Sock:
        client2Sock.send(("END").encode('utf-8'))
        client2Sock.close()

    #Closes connection to client 1
    client1Sock.close()

    print("Exiting")

if __name__ == "__main__":
    #Takes input of ports and IP addresses to call main function
    port1 = int(input("Please input the first client's port: "))
    port2 = int(input("Please input the second client's port: "))

    ip = input("Please input the local IPv4 address: ")

    main(ip, port1, ip, port2)