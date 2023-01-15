import time
from socket import *
import sys
import json
from threading import Thread

#Server would be running on the same host as Client

if len(sys.argv) != 2:
    print("\n===== Error usage, python3 cient3.py SERVER_PORT ======\n");
    exit(0);

serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

USERNAME = 'default'
exit_client = False

p2pSocket = socket(AF_INET, SOCK_STREAM)
p2pSocket.bind(("localhost", 0))
private_port = p2pSocket.getsockname()[1]
p2pSocket.listen()

p2pMap = {}

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(serverAddress)

def respond_message(field, message):
    clientSocket.send(
        json.dumps(
            {
                'header': 'response',
                field: message,
                'private_port': private_port
            }
        ).encode()
    )
    
def send_header(message):
    clientSocket.send(
        json.dumps(
            {
                'header': message
            }
        ).encode()
    )
    
def print_list(list):
    for item in list:
        print(item)
    
def login():
    global USERNAME
    while True:
        data = clientSocket.recv(1024)
        receivedMessage = json.loads(data.decode())["header"]
        
        if receivedMessage == "request_username":
            message = input("Username: ")
            message.strip()
            respond_message("username", message)
            USERNAME = message
        elif receivedMessage == "request_password":
            message = input("Password: ")
            respond_message("password", message)
        elif receivedMessage == "request_password_new":
            message = input("This is a new user. Enter a password: ")
            respond_message("password", message)
            
        elif receivedMessage == "password_wrong":
            print("Invalid Password. Please try again")
            continue
        elif receivedMessage == "password_blocked":
            print("Invalid Password. Your account has been blocked. Please try again later")
            exit(0)
        
        elif receivedMessage == "user_blocked":
            print("Your account is blocked due to multiple login failures. Please try again later")
            exit(0)
        elif receivedMessage == "user_already_logged_in":
            print("Your account has been logged in elsewhere. Please try again later")
            exit(0)
        
        elif receivedMessage == "welcome":
            print("==== Successful login. Welcome to David's messaging application! ====")
            break

login()

def receive():
    global exit_client 
    while True:
        if exit_client == True:
            return
        
        data = clientSocket.recv(1024)
        data = json.loads(data.decode())
        response = data['header']
        
        if data['header'] == 'broadcast_login':
            print(data['user'] + ' is now online.')
        elif data['header'] == 'broadcast_logout':
            print(data['user'] + ' is now offline.')
        elif data['header'] == 'broadcast_message':
            print("Broadcast from " + data['from'] + ": " + data['message'])
        
        elif data['header'] == 'message':
            print(data['message']) 
        elif data['header'] == 'message_failed':
            print(data['user'] + ' has blocked you, message failed.') 
        
            
        elif data['header'] == 'broadcast_failed':
            print("Failed to broadcast to the following users:")
            print_list(data['users'])
            
        elif data['header'] == 'list_users':
            print_list(data['users'])
            
        elif data['header'] == 'logout_success':
            print("You are now offline.")
            exit_client = True
        elif data['header'] == 'logout_timeout':
            print("Your connection has timed out.")
            exit_client = True
            
        elif data['header'] == 'blocked_already':
            print(data['user'] + " is already blocked.")
        elif data['header'] == 'blocked_self':
            print("Cannot block yourself.")
        elif data['header'] == 'blocked_success':
            print(data['user'] + " blocked.")
        elif data['header'] == 'blocked_invalid':
            print(data['user'] + " is an invalid user.")
            
        elif data['header'] == 'unblocked_already':
            print(data['user'] + " is already unblocked.")
        elif data['header'] == 'unblocked_self':
            print("Cannot unblock yourself.")
        elif data['header'] == 'unblocked_success':
            print(data['user'] + " unblocked.")
        elif data['header'] == 'unblocked_invalid':
            print(data['user'] + " is an invalid user.")
            
        elif data['header'] == 'private_request':
            if data['user'] in p2pMap:
                p2pMap[data['user']].send(
                    json.dumps(
                        {
                            'from': USERNAME,
                            'header': 'already'
                        }
                    ).encode()
                )
            else:
                print("Private chat request from " + data['user'] + ", (yes/no)?")
            
        elif response == 'private_decline':
            print(data['user'] + " has declined the private chat request.")
        elif response == 'user_invalid':
            print(data['user'] + " does not exist.")
        elif response == 'user_offline':
            print(data['user'] + " is offline.")
        elif response == 'private_self':
            print("You can't start a private chat with yourself.")
        elif response == 'private_blocked':
            print(data['user'] + " has blocked you. Cannot start private chat.")
        
        elif response == 'private_accept':
            username = data['user']
            host = 'localhost'
            port = int(data['port'])
            private_connect(host, port, username)
        elif response == 'private_decline':
            username = data['username']
            print(username + " declined the private chat.")
        elif response == 'private_confirmed':
            username = data['user']
            username = data['user']
            host = 'localhost'
            port = int(data['port'])
            private_connect(host, port, username)


receive_thread = Thread(name = "receiver", target = receive)
receive_thread.daemon = True
receive_thread.start()
       
def send():
    global exit_client
    while True:
        if exit_client == True:
            return
        
        user_input = input()
        message = user_input.strip().split()
        
        if message[0] == "logout":
            send_header("logout")
            
        elif message[0] == "whoelse":
            send_header("whoelse")
        elif message[0] == "whoelsesince":
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'whoelsesince',
                        'time': int(message[1])
                    }
                ).encode()
            )
            
        elif message[0] == "broadcast":
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'broadcast',
                        'message': user_input.replace("broadcast ", "", 1)
                    }
                ).encode()
            )
        elif message[0] == "message":
            text = ''
            for word in message[2:]:
                text = text + ' ' + word
            text = text[1:]
                
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'message',
                        'user': message[1],
                        'message': text
                    }
                ).encode()
            )
        
        elif message[0] == "block":
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'block',
                        'user': message[1]
                    }
                ).encode()
            )
        elif message[0] == "unblock":
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'unblock',
                        'user': message[1]
                    }
                ).encode()
            )
            
        elif message[0] == "startprivate":
            clientSocket.send(
                json.dumps(
                    {
                        'header': 'private_start',
                        'user': message[1]
                    }
                ).encode()
            )
        elif message[0] == "private":
            text = ''
            for word in message[2:]:
                text = text + ' ' + word
            text = text[1:]
            private_message(message[1], text)
                
        elif message[0] == "stopprivate":
            private_disconnect(message[1])
                
        elif message[0] == 'yes':
            clientSocket.send(
                    json.dumps(
                        {
                            'header': 'private_establish',
                        }
                    ).encode()
                )
            
        elif message[0] == 'no':
            clientSocket.send(
                    json.dumps(
                        {
                            'header': 'private_decline',
                        }
                    ).encode()
                )
            
        else:
            print("Invalid command: " + message[0])

send_thread = Thread(name = "sender", target = send)
send_thread.daemon = True
send_thread.start()

def private_responder(sock):
    def func():
        while True:
            data = sock.recv(1024)
            data = json.loads(data.decode())
            from_user = data["from"]
            header = data['header']
            if header == 'goodbye':
                print("Private chat with " + from_user + ' has been disconnected.')
                private_goodbye(from_user)
                break
            elif header == 'already':
                print(from_user + ' is already connected.')
                continue
            else:
                message = data["message"]
                print('[Private] ' + from_user + ': ' + message)
    return func

def private_connect(host, port, username):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host, port))
    p2pMap[username] = sock

def private_disconnect(user):
    if user in p2pMap:
        p2pMap[user].send(
            json.dumps(
                {
                    'from': USERNAME,
                    'header': 'goodbye'
                }
            ).encode()
        )
        p2pMap[user].close()
        p2pMap.pop(user)
    else:
        print('Stop chat failed. Not connected to ' + user)
        
def private_goodbye(user):
    if user in p2pMap:
        p2pMap[user].send(
            json.dumps(
                {
                    'from': USERNAME,
                    'header': 'goodbye'
                }
            ).encode()
        )
        p2pMap[user].close()
        p2pMap.pop(user)


def private_message(user, message):
    # send a private message to user
    if user in p2pMap and p2pMap[user]:
        p2pMap[user].send(
            json.dumps(
                {
                    'from': USERNAME,
                    'message': message,
                    'header': 'message'
                }
            ).
        encode())
    else:
        print('Message failed. Not connected to ' + user)
        
def receive_private():
    while True:
        sock, address = p2pSocket.accept()
        
        func = private_responder(sock)
        private_socket_thread = Thread(name=str(address), target=func)
        private_socket_thread.daemon = False
        
        print('Successfully connected to private chat.')
        private_socket_thread.start()

p_thread = Thread(name="PrivateRecvHandler", target=receive_private)
p_thread.daemon = True
p_thread.start()

while True:
    time.sleep(0.1)
    if exit_client == True:
        private_chats = []
        for user in p2pMap.copy():
            private_goodbye(user)
        print("=== exiting client ===")
        clientSocket.close()
        exit(0)
        
        

