import socket
from socket import socket, AF_INET, SOCK_STREAM
import string
from threading import Thread
from pathlib import Path
import os
import sys
import time

def ClientService(primarySock: socket, secondarySock: socket)->None:
    #Receives first request from client 1
    request = primarySock.recv(2048).decode('utf-8')

    #Loops until client 1 cancels program
    while not "END" in request.split()[0]:
        #Calls file request function if a request has been issued
        #Request Format: REQ fileName
        if(request.split()[0] == "REQ"):
            print(f"Requested Files {request.split()[1:]}")
            fileRequest(request.split()[1:], primarySock, secondarySock)

        #Takes in next request, if invalid assumes that the connection has been cancelled
        try:
            request = primarySock.recv(2048).decode('utf-8')
        except:
            request = "END"

    #If the client 2 connection is still valid, indicate to it that the connection is over and closes the connections
    if secondarySock:
        secondarySock.send(("END").encode('utf-8'))
        secondarySock.close()

    #Closes connection to client 1
    primarySock.close()


def fileRequest(files, primarySock: socket, secondarySock: socket)->None:
    for fileName in files:
        #Checks if the file exists on the server, requests from client 2 if it doesn't
        hadFile = True
        reqFile = Path(os.path.join(sys.path[0], fileName))

        if not reqFile.is_file():
            print(f"{fileName} not found, requesting from secondary client")
            hadFile = False

            #Sends request (REQ fileName) to client 2
            secondarySock.sendall(("REQ " + fileName).encode("utf-8"))

            #Receives 1024 of the file from client 2
            contents = bytearray(secondarySock.recv(1024))

            #Decodes 3-character tail from end of message
            #Tail is either EOF (end of file) or NEF (not end file)
            tail = contents[-3:]
            tailStr = tail.decode('utf-8')

            #Checks if the file was found in client 2
            if tailStr == "ERR":
                print("File not found, sending error")
                message = "File not found"
                primarySock.sendall((message + "ERR").encode('utf-8'))
                return

            #Removes tail from contents and writes to file
            contents = contents[: len(contents) - 3]

            file = open(os.path.join(sys.path[0], fileName), "wb")
            file.write(contents)

            #Loops until the tail is EOF, repeats same code as above
            while tailStr != "EOF":
                contents = bytearray(secondarySock.recv(1024))

                tail = contents[-3:]
                tailStr = tail.decode('utf-8')

                contents = contents[: len(contents) - 3]
                file.write(contents)

            file.close()

            print(f"{fileName} downloaded from secondary client")

        else:
            print(f"{fileName} found")
            
        #Begins to send file to client 1
        print(f"Sending file {fileName} to primary client")
        
        startTime = time.perf_counter()

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
        primarySock.sendall(contents)

        #Loop until counter reaches the total file size, repeat same code as above
        while currPos < fileSize:
            contents = bytearray(file.read(1021))
            currPos += len(contents)

            if currPos < fileSize:
                contents.extend("NEF".encode('utf-8'))
            else:
                contents.extend("EOF".encode('utf-8'))

            primarySock.sendall(contents)

        file.close()

        print(f"{fileName} sent to primary client")

        endTime = time.perf_counter()

        uploadRate = fileSize / (endTime - startTime)

        print(f"Upload Rate: {uploadRate} bytes per second")

        #Receives acknowledgement from client 1 (ACK fileName)
        response = primarySock.recv(2048).decode('utf-8')
        while response.split()[0] != "ACK" or response.split()[1] != fileName:
            response = primarySock.recv(2048).decode('utf-8')

        print(f"{fileName} acknowledged from primary client")

        #If file wasn't originally on server, deletes it
        if not hadFile:
            os.remove(os.path.join(sys.path[0], fileName))

def main(hostName: str, client1Port1: int, client1Port2: int, client2Port1: int, client2Port2: int)->None:
    print("Waiting for connections")

    #Connects to client 1
    server_sock1 = socket(AF_INET, SOCK_STREAM)
    server_sock1.bind((hostName, client1Port1))
    server_sock1.listen()

    client1Sock1, client1Addr1 = server_sock1.accept()

    server_sock2 = socket(AF_INET, SOCK_STREAM)
    server_sock2.bind((hostName, client1Port2))
    server_sock2.listen()

    client1Sock2, client1Addr2 = server_sock2.accept()

    print("Client 1 connected")

    #Connects to client 2
    server_sock3 = socket(AF_INET, SOCK_STREAM)
    server_sock3.bind((hostName, client2Port1))
    server_sock3.listen()

    client2Sock1, client2Addr1 = server_sock3.accept()

    server_sock4 = socket(AF_INET, SOCK_STREAM)
    server_sock4.bind((hostName, client2Port2))
    server_sock4.listen()

    client2Sock2, client2Addr2 = server_sock4.accept()

    print("Client 2 connected")

    client1Thread = Thread(target=ClientService, args=(client1Sock1, client2Sock2,))
    client2Thread = Thread(target=ClientService, args=(client2Sock1, client1Sock2,))

    client1Thread.start()
    client2Thread.start()

    client1Thread.join()
    client2Thread.join()

    print("Exiting")

if __name__ == "__main__":
    #Takes input of ports and IP addresses to call main function
    port1 = int(input("Please input the first client's primary port: "))
    port2 = int(input("Please input the first client's secondary port: "))

    port3 = int(input("Please input the second client's primary port: "))
    port4 = int(input("Please input the second client's secondary port: "))

    ip = input("Please input the local IPv4 address: ")

    main(ip, port1, port2, port3, port4)