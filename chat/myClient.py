import socket
import threading
import random

host = 'localhost' #'localhost' or "196.42.76.61"
serverPort = 12011
randomPort = random.randrange(1000,9999) #use random port if you are only using one computer to connect, otherwise you can enter your own port

global name
global ip
ip = 0
name = "name"

UDPclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # creating UDP socket
TCPclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket for server
TCPclient.connect((host, serverPort))

# receive various messages from the server
def receive():
    try:
        message = TCPclient.recv(2048).decode('ascii')
        # succesful login
        if "LGN0" in message:
            print("\nLogin successful.\n")
            print("Input one of the following server commands:\n1) MSG [username] (send message to user)\n2) LST (display connected clients)\n3) BLK [username] (block user from messaging you)\n4) EXT (disconnect from the server)\n")
            pass
        # failed log in
        if "LGN1" in message:
            print("Login failed, please try again.")
            login()
        # display user list
        if "LST0" in message:
            print("\nCurrent users in chat:")
            print(message[5:])
        # request to chat to user sent
        if "MSG0" in message:
            print("Message request sent to user. Waiting approval...")
            receive()  
        # chat request from a user
        if "MSG1" in message:  # connect to other user using UDP
            global name
            global ip
            address = message.split(":")
            name = address[1]
            print("Connected to " + name)
            ip = address[2] #"127.0.0.1" use your ip if you are using the same computer to host and connect
            port = address[3]
            UDPclient.bind((ip, randomPort))
            print("To exit the chat and return to the server, enter 'SERVER'")
            print("Enter message: ")
            udpReceiveThread = threading.Thread(daemon = True, target = UDPreceive)
            udpReceiveThread.start()
            UDPwrite(ip, port)
        # user not found 
        if "MSG2" in message:
            print("User not found.")
        # message received after blocking someone
        if "BLK" in message:
            print(message[5:] + " has been blocked from messaging you.")
        # user disconnecting from the server
        if "EXT0" in message:
            TCPclient.close()
            exit("\nDisconnected from the server.\n")
        
    except:
        TCPclient.close()
        exit("\nDisconnected from the server.\n")

# write function for sending commands to the server
def write():
    while True:
        message = input("Enter a server command: ")
        # exit the program
        if message == "EXT":
            TCPclient.send(message.encode("ascii"))
            TCPclient.close()
            UDPclient.close()
            exit("\nDisconnected from the server.\n")
        # check if user is messaging someone
        elif message[0:3] == "MSG" and len(message.split()) == 2:
            message = message + " " + str(ip) + " " + str(randomPort)
            TCPclient.send(message.encode("ascii"))
            receive()
        elif message == "LST":
            TCPclient.send(message.encode("ascii"))
            receive()
        elif message[0:3] == "BLK" and len(message.split()) == 2:
            TCPclient.send(message.encode("ascii"))
            receive()
        # prompt the user again if they input an invalid command
        else:
            print("Invalid server command.")
            write()

## UDP message connection
def UDPreceive(): # listen for UDP messages from other user
    while True:
        try:
            message, _ = UDPclient.recvfrom(2048)
            decodedMessage = message.decode("ascii")
            if decodedMessage == "ERROR859301": # arbitrary error number, just used to check if other user has disconnected
                print(name + " has disconnected.")
                print("Enter 'SERVER' to return to the server.")
                break
            else:
                print(name + ": " + decodedMessage)
        except:
            pass
        
def UDPwrite(ip, port): # function for writing to another user with a UDP connection
    while True:
        port = int(port)
        message = input("")
        if message == "SERVER": # exit UDP conncetion and return to TCP server connection
            print("Disconnecting from " + name + ", returning to server...")
            UDPclient.sendto(("ERROR859301").encode("ascii"),(ip, port))
            UDPclient.close()
            write()
            break
        UDPclient.sendto(message.encode("ascii"), (ip, port))
    
def login(): # login sequence for user
    nameString = input("Enter your name: ")
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    loginMessage = "LGN" + " " + nameString + " " + username + " " + password
    TCPclient.send(loginMessage.encode("ascii"))
    receive()

def main():
    print("Welcome to the server!\n")
    login()
    write()
    
if __name__ == "__main__":
    main()