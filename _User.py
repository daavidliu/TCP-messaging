from datetime import *


class User:
        def __init__(self, username, password, block_duration, timeout):
            self.username = username
            self.password = password
            
            self.block_duration = block_duration
            self.timeout = timeout
            
            self.is_online = False
            self.is_blocked = False
            
            self.consecutive_fail = 0
            
            self.when_unblocked = datetime(1, 1, 1)
            self.when_active = datetime(1, 1, 1)
            self.when_login = datetime(1, 1, 1)
            
            self.blocked_users = []
            self.offline_messages = []

        def authenticate(self, password):
            if self.is_blocked: return "user_blocked"
            if self.is_online: return "user_already_logged_in"
            
            if self.password == password:
                # correct password
                self.is_online = True
                self.when_login = datetime.now()
                self.when_active = datetime.now()
                self.consecutive_fail = 0
                return "welcome"
            else:
                # incorrect password
                self.consecutive_fail += 1
                if self.consecutive_fail >= 3:
                    self.when_unblocked = datetime.now() + timedelta(0, self.block_duration)
                    self.is_blocked = True
                    return "password_blocked"
                return "password_wrong"
            
        def offline_message(self, message):
            self.offline_messages.append(message)
            
        def empty_offline_messages(self):
            messages = self.offline_messages
            self.offline_messages.clear
            return messages
            
        def update(self):
            if self.when_unblocked < datetime.now():
                self.is_blocked = False
            if self.when_active + timedelta(0, self.timeout) < datetime.now():
                self.is_online = False
            
        def logout(self):
                self.is_online = False
                
        def whoelsesince(self, time):
            print(self.username + " log in time is " + self.when_login.strftime("%H:%M:%S"))
            if (self.when_login > datetime.now() - timedelta(0, time)):
                return True
            else:
                return False
            
        def block(self, username):
            if username in self.blocked_users:
                return 'blocked_already'
            elif username == self.username:
                return 'blocked_self'
            else:
                self.blocked_users.append(username)
                return 'blocked_success'
            
        def unblock(self, username):
            if username not in self.blocked_users:
                return 'unblocked_already'
            elif username == self.username:
                return 'unblocked_self'
            else:
                self.blocked_users.remove(username)
                return 'unblocked_success'
            
        def is_blocking(self, username):
            print(username)
            print(self.blocked_users)
            if username in self.blocked_users:
                print("returning true")
                return True
            else:
                print("returning false")
                return False
            
        def activate(self):
            self.when_active = datetime.now()