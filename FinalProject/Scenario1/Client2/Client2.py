from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import sys
from pathlib import Path

def fileRequest(fileName: str, conn: socket)->None:
    #Make sure the requested file is valid
    reqFile = Path(os.path.join(sys.path[0], fileName))

    if reqFile.is_file():
        #Begin sending file
        print(f"Sending {fileName}")

        #Opens file, logs size of file, and begins counter for position in file
        file = open(os.path.join(sys.path[0], fileName), "rb")
        fileSize = os.path.getsize(os.path.join(sys.path[0], fileName))
        currPos = 0

        #Reads first 1021 bytes of the file, increments counter
        contents = bytearray(file.read(1021))
        currPos += len(contents)

        #Appends tail onto contents and sends data to server
        #NEF (not end file) or EOF (end of file)
        if currPos < fileSize:
            contents.extend("NEF".encode('utf-8'))
        else:
            contents.extend("EOF".encode('utf-8'))

        conn.sendall(contents)

        #Loops until entire file has been sent, repeats above code
        while currPos < fileSize:
            contents = bytearray(file.read(1021))
            currPos += len(contents)

            if currPos < fileSize:
                contents.extend("NEF".encode('utf-8'))
            else:
                contents.extend("EOF".encode('utf-8'))

            conn.sendall(contents)

        file.close()
    else:
        #Sends an error to the server if file not found
        print("File not found, sending error")
        message = "File not found"
        conn.sendall((message + "ERR").encode('utf-8'))
        return

    print(f"{fileName} sent")

def main(hostname: str, portno: int)->None:
    #Connects to server
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    print("Connected to server")

    #Receives request from server
    request = conn.recv(2048).decode("utf-8")

    #Makes sure that request actually received something, skips if it didn't
    if sys.getsizeof(request) >= sys.getsizeof("END"):
        #Loops until server indicates the program is terminated, or until request is invalid
        while request.split()[0] != "END" or sys.getsizeof(request) == 0:
            #If server submitted a valid request (REQ fileName), use the file request function
            if(request.split()[0] == "REQ"):
                print(f"{request.split()[1]} requested")
                fileRequest(request.split()[1], conn)

            request = conn.recv(2048).decode("utf-8")

    #Close connection with server after receiving "END" or an invalid request
    conn.close()

    print("Exiting")

if __name__ == "__main__":
    #Takes port number and IP address of the server as input
    ip = input("Please input the IPv4 address of the server: ")
    port = int(input("Please input the port to connect: "))

    main(ip, port)