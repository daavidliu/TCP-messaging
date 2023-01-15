from socket import *
from threading import Thread
import sys, select
import time
from typing import Dict
import json

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket, server):
        Thread.__init__(self)
        self.server = server
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        
        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True
        
    def run(self):
        self.initiate_login()
        self.server.add_thread(self, self.user)
        
        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.receive_data()
            header = data['header']
            
            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if header == '' or header == 'logout':
                self.terminate_connection()
                break
            
            elif header == "whoelse":
                users = self.server.online_users(self.user)
                users.remove(self.user)
                self.send_users_list(users)
            elif header == "whoelsesince":
                users = self.server.whoelsesince_users(data['time'], self.user)
                if self.user in users:
                    users.remove(self.user)
                self.send_users_list(users)
                
            elif header == "broadcast":
                print("Broadcasting message from " + self.user + ": " + data['message'])
                failed = self.server.broadcast_message(data['message'], self.user)
                if (failed):
                    self.clientSocket.send(
                    json.dumps(
                        {
                            'header': "broadcast_failed",
                            'users': failed
                        }
                    ).encode()
                )
            elif header == "message":
                success = self.server.message(data['message'], self.user, data['user'])
                if (not success):
                    self.clientSocket.send(
                    json.dumps(
                        {
                            'header': "message_failed",
                            'user': data['user']
                        }
                    ).encode()
                )
                
            elif header == "block":
                print(self.user + " is blocking " + data['user'])
                response = self.server.block(self.user, data['user'])
                self.clientSocket.send(
                    json.dumps(
                        {
                            'header': response,
                            'user': data['user']
                        }
                    ).encode()
                )
            elif header == "unblock":
                print(self.user + " is unblocking " + data['user'])
                response = self.server.unblock(self.user, data['user'])
                self.clientSocket.send(
                    json.dumps(
                        {
                            'header': response,
                            'user': data['user']
                        }
                    ).encode()
                )
                
            elif header == "private_start":
                print(self.user + " requesting private chat with " + data['user'])
                response = self.server.request_private(self.user, data['user'])
                
                if response == 'private_requesting':
                    self.server.threads[data['user']].request_private(self)
                else:
                    print("sending response " + response)
                    self.clientSocket.send(
                        json.dumps(
                            {
                                'header': response,
                                'user': data['user'],
                            }
                        ).encode()
                    )
                
                print("ending startprivate")
                continue
            
            elif header == "private_establish":
                
                if self.user in self.server.private_requests:
                    print("private establish!!!")
                    sender = self.server.private_requests[self.user]
                    self.server.threads[sender].private_accept(self.user)
                    self.clientSocket.send(
                        json.dumps(
                            {
                                'header': 'private_confirmed',
                                'user': sender,
                                'port': self.server.threads[sender].private_port
                            }
                        ).encode()
                    )
                    
            elif header == "private_decline":
                if self.user in self.server.private_requests:
                    print("private accept!!!")
                    sender = self.server.private_requests[self.user]
                    self.server.threads[sender].private_reject(self.user)
                
            else:
                print("invalid command: " + header)
                continue
            
            self.server.activate_user(self.user)
                
        return
    
    def terminate_connection(self):
        self.clientAlive = False
        self.server.remove_thread(self.user)
        
        self.send_header("logout_success")
        print("sent logout_success to client")
        
        print("===== the user disconnected - ", self.clientAddress)
        
    def private_reject(self, recipient):
        print("[send] reject private request to " + recipient)
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'private_decline',
                    'user': recipient
                }
            ).encode()
        )
        
    def private_accept(self, recipient):
        print("[send] accept private request to " + recipient)
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'private_accept',
                    'user': recipient,
                    'port': self.server.threads[recipient].private_port
                }
            ).encode()
        )
        
    def connection_timeout(self):
        self.clientAlive = False
        self.server.remove_thread(self.user)
        
        self.send_header("logout_timeout")
        print("sent timeout to client")
        print("===== the user disconnected - ", self.clientAddress)
            
    def send_header(self, message):
        print("[send] " + message)
        self.clientSocket.send(
            json.dumps(
                {
                    'header': message
                }
            ).encode()
        )
        
    def send_users_list(self, users):
        print("[send] users list")
        self.clientSocket.send(
            json.dumps(
                {
                    'header': "list_users",
                    "users": users
                }
            ).encode()
        )
        
    def receive_data(self):
        data = self.clientSocket.recv(1024)
        data = json.loads(data.decode())
        return data
    
    def initiate_login(self):
        # request username from the client
        self.send_header("request_username")
        data = self.receive_data()
        username = data["username"]
        
        self.private_port = data['private_port']
        
        if self.server.has_user(username):
            self.request_password(username)
        else:
            self.new_user(username)
            
    def request_password(self, username):
        # request password from the client
        self.send_header("request_password")
        data = self.receive_data()
        print(data)
        password = data["password"]
        
        message = self.server.login(username, password)
        self.send_header(message)
        
        if (message == "welcome"):
            self.user = username
        elif (message == "password_wrong"):
            self.request_password(username)
        else:
            exit(0)
            
    def new_user(self, username):
        # request password from the client
        self.send_header("request_password_new")
        data = self.receive_data()
        password = data["password"]
        
        message = self.server.register(username, password)
        self.send_header(message)
        
        self.user = username
        
    def broadcast_login(self, username):
        print("[send] broadcasting login of " + username + " to " + self.user)
        
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'broadcast_login',
                    'user': username
                }
            ).encode()
        )
        
    def broadcast_logout(self, username):
        print("[send] broadcasting logout of " + username + " to " + self.user)
        
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'broadcast_logout',
                    'user': username
                }
            ).encode()
        )
        
    def broadcast_message(self, message, username):
        print("broadcasting to " + self.user)
        
        if username == self.user:
            return 
        
        print("[send] broadcasting from " + username + " to " + self.user)
        
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'broadcast_message',
                    'message': message,
                    'from': username
                }
            ).encode()
        )
        
    def message(self, message):
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'message',
                    'message': message
                }
            ).encode()
        )
        
    def send_all_messages(self, messages):
        for message in messages:
            self.message(message)
            
    def request_private(self, thread):
        print("thread is requesting")
        self.clientSocket.send(
            json.dumps(
                {
                    'header': 'private_request',
                    'user': thread.user,
                    'host': thread.clientSocket.getsockname()[0],
                    'port': thread.private_port
                }
            ).encode()
        )
        
        
        