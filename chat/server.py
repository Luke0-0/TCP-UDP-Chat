from socket import *
import threading
from Client import *

# SERVER INITIATION:

clients = {}
dict_lock = threading.Lock()
HOST_IP = 'localhost'
HOST_PORT = 12000

connectorSocket = socket(AF_INET, SOCK_STREAM)
connectorSocket.bind((HOST_IP, HOST_PORT))
connectorSocket.listen()
print(f"The server is running and listening for connections on {HOST_IP}:{HOST_PORT}")

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# Function runs continuosly accepting connections on connectorSocket while server is running
# When a connection is made print the address to the server
# Create a thread to handle each client individually so they can talk to the server concurrently
def acceptClients():
    while True:
        try:
            clientSocket, addr = connectorSocket.accept()
            print(f"Accepted connection from {addr}")
            clientThread = threading.Thread(target=handleClient, args=(clientSocket, addr))
            clientThread.start()
        except:
            print("Error accepting connection from client.")


# Function to handle clients in separate threads
# Parse client socket and address
# Handles all requests sent to server from individual clients
# Sends back appropriate response codes depending on request types
# This is where the protocol is implemented
def handleClient(sock, addr):

    client_username = 'noSignedIn' # Default username

    while True:
        request = sock.recv(1024).decode().split() #Convert message from client to server into str[] of args
        requestType = request[0] #All requests must start with a code to identify request types

        #* LOGIN request
        # Protocol: [RequestType, clientName, clientUsername, secretCode]
        # Check if client exists, if not, create client object and add to clients{}
        if requestType == 'LGN':
            print(f"Attempting login on {request[2]}")

            # Take in arguments
            name = request[1]
            username = request[2]
            secret = request[3]

            client_username = username # store client username in thread for future use

            # Print to server:
            print(f"CLIENT_NAME: {name}")
            print(f"CLIENT_USERNAME: {username}")
            print(f"CLIENT_SECRET: {secret}")

            # Check to see if client already exists
            if username not in clients.keys():

                newClient = Client(name, username, secret, addr, sock, 'OFFLINE') # create new clients

                with dict_lock: # use lock to ensure thread safety
                    clients[username] = newClient
                    print(f"New client {username} has logged in.")
                    # Send succesfull NEW login response to client
                    response = f"LGN0:{username}:{addr[0]}"
                    sock.send(response.encode())
                    clients[client_username].updateState('ONLINE')
            else:
                if clients[username].secret == secret:
                    print(f"{username} has logged in succesfully.")
                    # Send succesfull login response to client
                    response = f"LGN0:{username}:{addr[0]}"
                    sock.send(response.encode())
                    clients[client_username].updateState('ONLINE')
                else:
                    # Send failed login response to client
                    print(f"Failed login attempt on {username} at {addr}.")
                    response = f"LGN1:Failed login attempt on {username} at {addr}."
                    sock.send(response.encode())
                    clients[client_username].updateState('OFFLINE')

        #* MESSAGE request
        # Protocol: [RequestType, peer_username, clientUDP_IP, clientUDP_PORT]
        # Check if client exists, if not, create client object and add to clients{}
        elif requestType == 'MSG':

            # Take in arguments
            peer_username = request[1]
            clientIP = request[2]
            clientPORT = request[3]

            # Print to server:
            print(f"REQUESTED_PEER: {peer_username}")

            requestedPeer = clients[peer_username]
            peer_state = requestedPeer.state.split(':')
            available = False

            if peer_state[0] == "IN_CHAT":
                if peer_state[1] == client_username:
                    available = True
            elif peer_state[0] == "ONLINE":
                available = True

            # Check if peer exists
            if (peer_username in clients.keys()) and (client_username not in requestedPeer.blocklist) and (available):
                peerSock = requestedPeer.socket # Get peer's TCP socket for server contact

                #* MSG Response code:
                # MSG0 signals that UDP socket information has been sent to peer, and client must wait for a response.
                # MSG1 signals that message contains UDP socket information and client can begin sending messages to peer via UDP
                clientAddr_str = f"MSG1:{client_username}:{clientIP}:{clientPORT}"
                response = f"MSG0:{peer_username}" 

                sock.send(response.encode())
                peerSock.send(clientAddr_str.encode())
                clients[client_username].updateState(f"IN_CHAT:{peer_username}")
            else:
                # If peer does not exist send back error code 'MSG2'
                error = f"There is no {peer_username} on the server."
                print(error)
                response = f"MSG2:{error}"
                sock.send(response.encode())

        #* LIST request
        # Protocol: [requestType] (No additional arguments)
        # Create \n separated list of clients on server
        # Send to client for printing
        elif requestType == 'LST':
            clientList = ''
            for peer_username in clients.keys():
                if client_username not in clients[peer_username].blocklist:
                    clientList += str(clients[peer_username].username)+"\n"
            clientList = clientList[:-1] # Remove last newline
            response = f"LST0:{clientList}" # Send back response with list as str
            sock.send(response.encode())

        #* EXIT request
        # Protocol: [requestType] (No additional arguments)
        # Remove client from server
        elif requestType == 'EXT':
            clients.pop(client_username) # Remove client from clients{}
            print(f"{client_username} has disconnected from the server.")
            response = 'EXT0'
            sock.send(response.encode())
            return # Return to close thread
        
        #* BLOCK request
        # Protocol: [requestType, peer_username]
        # Block peer from contacting client by added them to client.blocklist
        elif requestType == 'BLK':
            peer_username = request[1]
            clients[client_username].blocklist.append(peer_username)
            print(f"{peer_username} has been blocked from contacting {client_username}")
            response = f"BLK0:{peer_username}"
            sock.send(response.encode())

def main():
    acceptClients()

if __name__ == "__main__":
    main()