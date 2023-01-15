from socket import *
import sys
from threading import Thread
from _ClientThread import ClientThread
from _User import User
import time

# acquire server host and port from command line parameter

if len(sys.argv) != 4:
    print("\n===== Error usage, python3 server.py server_port block_duration timeout ======\n")
    exit(0)


serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

block_duration = int(sys.argv[2])
timeout = int(sys.argv[3])

# This line creates the server’s socket. 
# The first parameter indicates the address family; 
# in particular,AF_INET indicates that the underlying network is using IPv4.
# The second parameter indicates that the socket is of type SOCK_STREAM,
# which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM).
serverSocket = socket(AF_INET, SOCK_STREAM)

# The above line binds (that is, assigns) the port number 12000 to the server’s socket. 
# In this manner, when anyone sends a packet to port 12000 at the IP address of the server (localhost in this case), 
# that packet will be directed to this socket.
serverSocket.bind(serverAddress)

class Server(Thread):
    # manage all user data, including credentials, block status,
    # user-to-user block status, time out, online status,
    # and last login status

    def __init__(self, block_duration, timeout):
        Thread.__init__(self)
        self.users = {}
        self.block_duration = block_duration
        self.timeout = timeout
        self.load_credentials()
        self.threads = {}
        self.private_requests = {}
    
    def run(self):
        while True:
            time.sleep(1)
            self.refresh()
    
    def add_thread(self, thread, username):
        for user in self.threads:
            if self.users[username].is_blocking(user):
                continue
            self.threads[user].broadcast_login(username)
            
        self.threads[username] = thread
        messages = self.users[username].empty_offline_messages()
        thread.send_all_messages(messages)
        
    def remove_thread(self, username):
        self.threads.pop(username)
        self.users[username].logout()
        for user in self.threads:
            if self.users[username].is_blocking(user):
                continue
            self.threads[user].broadcast_logout(username)
        print(username + " has logged out")

    def load_credentials(self):
        try:
            with open("credentials.txt", "r") as credentials:
                for credential in credentials:
                    username, password = credential.strip().split()
                    self.users[username] = User(username, password, block_duration, timeout)
                    
        except:
            print("Error loading credentials.")
            exit(1)
            
    def add_credentials(self, username, password):
        try:
            with open("credentials.txt", "a") as credentials:
                credentials.write("\n" + username + " " + password)
                    
        except:
            print("Error adding credentials.")
            exit(1)
            
    def has_user(self, username):
        if username in self.users.keys():
            return True
        else:
            return False
        
    def login(self, username, password):
        if username in self.users.keys():
            return self.users[username].authenticate(password)
        else:
            return "username_invalid"
        
    def register(self, username, password):
        self.users[username] = User(username, password, block_duration, timeout)
        self.add_credentials(username, password)
        return self.login(username, password)

    def has_user(self, username):
        return username in self.users

    def is_online(self, username):
        return username in self.users and self.users[username].is_online

    def refresh(self):
        for username in self.users:
            self.users[username].update()
            if username in self.threads and not self.users[username].is_online:
                self.threads[username].connection_timeout()
            
    def online_users(self, asker):
        online_users = []
        for username in self.users:
            if self.users[username].is_blocking(asker):
                continue
            elif self.users[username].is_online:
                online_users.append(username)
                
        return online_users
    
    def whoelsesince_users(self, time, asker):
        users = []
        for username in self.users:
            if self.users[username].is_blocking(asker):
                continue
            elif self.users[username].whoelsesince(time):
                users.append(username)
                
        return users
    
    def broadcast_message(self, message, username):
        print("server is broadcasting the message")
        failed = []
        for user in self.threads:
            if self.users[user].is_blocking(username):
                failed.append(user)
            else:
                self.threads[user].broadcast_message(message, username)
        return failed
            
    def block(self, user, blocked_user):
        if blocked_user not in self.users:
            return 'blocked_invalid'
        else:
            return self.users[user].block(blocked_user)
    def unblock(self, user, blocked_user):
        if blocked_user not in self.users:
            return 'unblocked_invalid'
        else:
            return self.users[user].unblock(blocked_user)
        
    def message(self, message, sender, recipient):
        text = sender + ': ' + message
        if self.users[recipient].is_blocking(sender):
            return False
        elif self.users[recipient].is_online:
            self.threads[recipient].message(text)
        else:
            self.users[recipient].offline_message(text)
        
        print("message returning true")
        return True
    
    def activate_user(self, username):
        self.users[username].activate()
        
    def request_private(self, sender, recipient):
        print("server is requesting")
        if recipient not in self.users:
            print("user_invalid")
            return 'user_invalid'
        elif not self.users[recipient].is_online:
            print("user_offline")
            return 'user_offline'
        elif sender == recipient:
            print("private_self")
            return 'private_self'
        elif self.users[recipient].is_blocking(sender):
            print("private_blocked")
            return 'private_blocked'
        
        self.private_requests[recipient] = sender
        return 'private_requesting'
        
    
            
        


print("\n===== Server is running =====")
server = Server(block_duration, timeout)
server.start()

while True:
    print("===== Waiting for connection request from clients...=====")
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt, server)
    clientThread.start()
