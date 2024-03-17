class Client:
    def __init__(self, name, username, secret, address, socket, state):
        self.name = name
        self.username = username
        self.secret = secret
        self.address = address
        self.socket = socket
        self.state = state
        self.blocklist = []

    def addMessageRequest(self, messageRequest):
        self.inbox.add(messageRequest)
    
    def updateState(self, state):
        self.state = state
        
    def __str___(self):
        return self.username