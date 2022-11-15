from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from pathlib import Path
import os
import sys

def main(hostname: str, portno: int)->None:
    #Connects to server
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    print("Connected to server")

    #Asks for file name as input, loops until user inputs "quit"
    fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")

    while fileName.lower() != "quit":
        #Checks if the file already exists, skips to next iteration if so
        if Path(os.path.join(sys.path[0], fileName)).is_file():
            print(f"{fileName} already exists")
            fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")
            continue
        
        #Creates request message for server (REQ fileName) and sends it
        message = "REQ " + fileName
        conn.sendall(message.encode('utf-8'))

        print(f"Requested {fileName}")

        f = open(os.path.join(sys.path[0], fileName), "wb")

        #Receives first set of bytes from server
        contents = bytearray(conn.recv(1024))

        #Decodes tail, either NEF (not end file) or EOF (end of file)
        tail = contents[-3:]
        tailStr = tail.decode('utf-8')

        #Removes tail from contents and writes to file
        contents = contents[: len(contents) - 3]
        f.write(contents)

        #Continues to receive file until tail is "EOF", repeats above code
        while tailStr != "EOF":
            contents = bytearray(conn.recv(1024))

            tail = contents[-3:]
            tailStr = tail.decode('utf-8')

            contents = contents[: len(contents) - 3]
            f.write(contents)

        f.close()

        print(f"Received {fileName}")

        #Sends acknowledgement to server (ACK fileName)
        conn.sendall(("ACK " + fileName).encode('utf-8'))

        print(f"Acknowledged {fileName}")

        #Asks for next iteration's input
        fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")

    #After user inputs "quit", sends message cancelling program to server and closes connection
    message = "END"
    conn.sendall(message.encode('utf-8'))

    conn.close()

    print("Exiting")

if __name__ == "__main__":
    #Takes port and server IP as input for main function
    ip = input("Please input the IP address of the server: ")
    port = int(input("Please input the port to connect: "))

    main(ip, port)