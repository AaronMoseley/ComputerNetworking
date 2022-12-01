import socket
from socket import socket, AF_INET, SOCK_STREAM
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
        files = []
        #Calls file request function if a request has been issued
        #Request Format: REQ file1Name, file2Name...
        if(request.split()[0] == "REQ"):
            print(f"Requested File {request.split()[1:]}")
            #Processes one request argument at a time
            files.append( primeServer(request.split()[1:], primarySock, secondarySock) )
        
        sendFiles(files, primarySock, secondarySock)

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


def primeServer(files, primarySock: socket, secondarySock: socket)->None:
    #For converting files later
    filesWithDeleteInfo = []

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

            try:
                tailStr = tail.decode('utf-8')
            except:
                tailStr = "NAN"

            while len(contents) < 1024 and tailStr != "NEF" and tailStr != "EOF" and tailStr != "ERR":
                contents.extend(bytearray(secondarySock.recv(1024 - len(contents))))

                tail = contents[-3:]
                try:
                    tailStr = tail.decode('utf-8')
                except:
                    tailStr = "NAN"

            #Checks if the file was found in the server or client 2, advances if not
            if tailStr == "ERR":
                print(f"{fileName} not found")
                continue

            #Removes tail from contents and writes to file
            contents = contents[: len(contents) - 3]

            file = open(os.path.join(sys.path[0], fileName), "wb")
            file.write(contents)

            #Loops until the tail is EOF, repeats same code as above
            while tailStr != "EOF":
                contents = bytearray(secondarySock.recv(1024))

                tail = contents[-3:]
                try:
                    tailStr = tail.decode('utf-8')
                except:
                    tailStr = "NAN"

                while len(contents) < 1024 and tailStr != "NEF" and tailStr != "EOF":
                    contents.extend(bytearray(secondarySock.recv(1024 - len(contents))))

                    tail = contents[-3:]
                    try:
                        tailStr = tail.decode('utf-8')
                    except:
                        tailStr = "NAN"

                tail = contents[-3:]
                tailStr = tail.decode('utf-8')

                contents = contents[: len(contents) - 3]

                file.write(contents)

            file.close()

            print(f"{fileName} downloaded from secondary client")

        else:
            print(f"{fileName} found")
        
        #Files are converted to tuples which also keep track of server ownership status.
        filesWithDeleteInfo.append( (fileName, hadFile) )

    return filesWithDeleteInfo


def sendFiles(flaggedFiles, primarySock: socket, secondarySock: socket)->None:
    #Files are now of [(file1Name, hadFile1), (file2Name, hadFile2)...] format
    for i, fileEntry in enumerate(flaggedFiles):  
        #Begins to send file to client 1
        print(f"Sending file {fileEntry[i][0]} to primary client")
        
        startTime = time.perf_counter()

        file = open(os.path.join(sys.path[0], fileEntry[i][0]), "rb")

        #Logs size of file and starts a counter
        fileSize = os.path.getsize(os.path.join(sys.path[0], fileEntry[i][0]))
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

        print(f"{fileEntry[i][0]} sent to primary client")

        endTime = time.perf_counter()

        uploadRate = fileSize / (endTime - startTime)

        print(f"Upload Rate: {uploadRate} bytes per second")
    
    for i, fileEntry in enumerate(flaggedFiles):
        #Receives acknowledgement from client 1 (ACK fileEntry)
        response = primarySock.recv(2048).decode('utf-8')
        while response.split()[0] != "ACK" or response.split()[1] != fileEntry[i][0]:
            response = primarySock.recv(2048).decode('utf-8')

        print(f"{fileEntry[i][0]} acknowledged from primary client")

        #If file wasn't originally on server, deletes it
        if not fileEntry[i][1]:
            os.remove(os.path.join(sys.path[0], fileEntry[i][0]))



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