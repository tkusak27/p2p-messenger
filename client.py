import socket, json, sys

class P2PClient(object):

    def __init__(self, hostname, port, auto_run_handler = True):
        '''
        Create a P2PClient object. 

        args:
            hostname (str): The IP address of the central server that stores room information.
            port (int): The port where the central server is running. 
            auto_run_handler (bool): Set to False for stress testing, otherwise leave untouched.
        '''
        self.hostname = hostname
        self.port = port
        self.room = None
        self.peers = None

        if auto_run_handler:
            self.main_handler()


    def main_handler(self):
        '''
        The main handler for the P2PClient object. Will constantly monitor the standard input
        for user input. The handler will start by prompting the user with the options to either:
            A. List the public rooms
            B. Join a room
            C. Create a room
        Once a client has joined a room, all input that starts with a ':' (colon) will be **command** 
        input that handles the clients state. All other input will be treated as a message.
        '''
        print("StudyChat P2P client has been started!\n")
        print("To get started, please select one of the options below by typing the corresponding letter and pressing enter.")
        user_input = self.display_menu()
        print(f"user input is {user_input}")
        match user_input:
            # list public rooms
            case "A":
                pass
            # join a room
            case "B":
                if self.join_handler():
                    self.chat_handler()
            # create a room
            case "C":
                print("Case C!")
                if self.create_handler():
                    # should already be a part of the room, so just run chat handler
                    self.chat_handler()
                else:
                    print("Error: Please restart the program.")
                    return
                
            case "Q":
                return


    def create_handler(self):
        '''
        Basic handler for user input when "create room" is selected.
        '''
        print("Please enter the name of the room you wish to create: ", end="")

        room_name = sys.stdin.readline().strip()
        return self.create_room(room_name)


    def join_handler(self):
        '''
         Basic handler for user input when "join room" is selected.
        '''
        print("Please enter the name of the room you wish to join: ")
        print("Input: ", end="")

        room_name = sys.stdin.readline().strip()
        return self.join_room(room_name)
    

    def chat_handler(self):
        pass



    def display_menu(self):
        '''
        Displays the initial menu and returns the user's response.
        '''
        while True:
            print("\tA. List public rooms")
            print("\tB. Join a room")
            print("\tC. Create a room")
            print("\tQ. Quit this application\nInput: ", end="")

            option = sys.stdin.readline().strip().upper()
            if option in {"A", "B", "C", "Q"}:
                return option
            else:
                print(f"'{option}' is not a valid option. Please try again.")


    def connect_to_central_server(self, hostname=None, port=None):
        '''
        Connects the P2PClient object to the central server.

        args:
            hostname (str): IP address of the central server.
            port (int): Port of the central server.
        '''
        if not hostname:
            hostname = self.hostname
        if not port:
            port = self.port
        
        try:
            print(f"Attempting to connect to {self.hostname}:{port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5) 
            client_socket.connect((hostname, port))
            print(f"Connected to server on {hostname}:{port}")
            return client_socket
        except(socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
            client_socket.close()

    
    def handle_message(self):
        # need to implement, basically consolidate the following functions to re-use code
        pass


    def join_room(self, room):
        '''
        Joins a specified room.

        args:
            room (str): Identifier of the room the client wishes to join.
        '''
        try:
            client_socket = self.connect_to_central_server(self.hostname, self.port)
            if not client_socket:
                print(f"Error creating socket connection to {self.hostname}:{self.port}")
                return False
            
            join_request = {
                "action": "join",
                "room": room
            }

            client_socket.sendall(json.dumps(join_request).encode("utf-8"))
            print(f"Sent join request: {join_request}")

            while True:
                message = client_socket.recv(1024)
                if message:
                    response = json.loads(message.decode("utf-8"))

                    if response["status"] == "success":
                        print(f"Server successfully joined {room}")
                        self.rooms = room
                        self.peers = response["ips"]
                        return True
                    
                    else:
                        print(f"Server failed to receive info of {room}")
                        return False

                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()
        

    def create_room(self, room):
        '''
        Create a room for client-to-client interaction.

        args:
            room (str): Identifier of the room the client wishes to create.
        '''
        print(f"Attempting to create room {room}...")
        try:
            client_socket = self.connect_to_central_server(self.hostname, self.port)
            if not client_socket:
                print(f"Error creating socket connection to {self.hostname}:{self.port}")
                return False
            
            join_request = {
                "action": "create",
                "room": room
            }
            client_socket.sendall(json.dumps(join_request).encode("utf-8"))

            while True:
                message = client_socket.recv(1024)
                if message:
                    response = json.loads(message.decode("utf-8"))

                    if response["status"] == "success":
                        print(f"Server successfully created room {room}")
                        self.room = room
                        return True
                    
                    else:
                        print(f"Server failed to create room {room}")
                        return False
        
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()

    def leave_room(self, room):
        '''
        Get the client to leave the room

        args:
            room (str): Identifier of the room the client wishes to leave.
        '''
        try:
            client_socket = self.connect_to_central_server(self.hostname, self.port)
            if not client_socket:
                print(f"Error creating socket connection to {self.hostname}:{self.port}")
                return False
            
            join_request = {
                "action": "create",
                "room": room
            }
            client_socket.sendall(json.dumps(join_request).encode("utf-8"))
            print(f"Sent create request: {join_request}")

            while True:
                message = client_socket.recv(1024)
                if message:
                    response = json.loads(message.decode("utf-8"))

                    if response["status"] == "success":
                        print(f"Server successfully removed client from room {room}")
                        self.room = None
                        return True
                    
                    else:
                        print(f"Server failed to remove client from room {room}")
                        return False
        
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()

    def send_message(self, msg):
        '''
        Join a room and give the user the ability to send/receive messages from room members.

        args:
            room (str): Name of the room
        '''
        if not self.room:
            print("You must join a room before sending a message.")
            return False

        if not self.peers:
            print("No peers available to send messages to.")
            return False

        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            for peer in self.peers:
                ip, port = peer
                try:
                    udp_socket.sendto(msg.encode('utf-8'), (ip, port))
                    print(f"Message sent to {ip}:{port}")
                except Exception as e:
                    print(f"Failed to send message to {ip}:{port}: {e}")
        except Exception as e:
            print(f"An error occurred while sending messages: {e}")
        finally:
            udp_socket.close()



if __name__ == "__main__":
    target_hostname = "student12.cse.nd.edu"
    target_port = 12345
    client = P2PClient(target_hostname, target_port)