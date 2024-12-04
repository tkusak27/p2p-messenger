import socket, json, sys, select

class P2PClient(object):

    def __init__(self, hostname, port, auto_run_handler = True):
        '''
        Create a P2PClient object. 

        args:
            hostname (str): The IP address of the central server that stores room information.
            port (int): The port where the central server is running. 
            auto_run_handler (bool): Set to False for stress testing, otherwise leave untouched.
        '''
        self.server_hostname = hostname
        self.server_port = port
        self.server_socket = None
        self.room = None
        self.peers = []
        self.running = False
        self.address = None
        self.port = None
        self.user_id = None

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
        print("To get started, please create a username: ", end="", flush=True)
        self.user_id = sys.stdin.readline().strip()
        print("Now select one of the options below by typing the corresponding letter and pressing enter.")
        user_input = self.display_menu()

        # used to be match statement but wasn't working
        # list public rooms
        if user_input == "A":
            pass

        # join a room
        elif user_input == "B":
            out = self.join_handler()
            if out: 
                self.running = True
                self.chat_handler()

        # create a room
        elif user_input == "C":
            print("Please enter the name of the room you wish to create: ", end="", flush=True)
            room_name = sys.stdin.readline().strip()
            if room_name and self.create_room(room_name):
                self.running = True
                self.chat_handler()
            else:
                print("Error: Please restart the program.")
                return
            
        elif user_input == "Q":
            return


    def join_handler(self):
        '''
        Basic handler for user input when "join room" is selected.
        '''
        print("\nPlease enter the name of the room you wish to join.\nInput:", end="", flush=True)

        room_name = sys.stdin.readline().strip()
        return self.join_room(room_name)
    

    def chat_handler(self):
        '''
        Key handler which handles all chat communication, such as sending and receiving
        messages
        '''
        # assuming we have already joined the room and have the ips
        print(f"Opening chatroom {self.room}...")
        print(f"{len(self.peers)} peers are here now.")
        print("Type 'exit' to leave the chatroom.")
        print("> ", end="", flush=True)

        self.running = True

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.port)) 

        try:
            while self.running:
                readable, _, _ = select.select([sys.stdin, udp_socket], [], [])

                for source in readable:
                    if source == udp_socket:
                        data, addr = udp_socket.recvfrom(1024)
                        msg = json.loads(data.decode('utf-8'))
                        if "status" in msg and msg["status"] == "update":
                            self.peers = [tuple(peer) for peer in msg["clients"]]
                        else:
                            print(f'\n{msg["user"]}: {msg["body"]}')
                            print("> ", end="", flush=True)


                    elif source == sys.stdin: 
                        message = sys.stdin.readline().strip()
                        if message.lower() == "exit":
                            print("Exiting chatroom...")
                            self.running = False
                            break
                        
                        print("> ", end="", flush=True)

                        for peer in self.peers:
                            if peer != (self.address, self.port):
                                try:
                                    send_msg = {
                                        "user": self.user_id,
                                        "body": message
                                    }
                                    json_send_msg = json.dumps(send_msg)
                                    udp_socket.sendto(json_send_msg.encode('utf-8'), tuple(peer))

                                except Exception as e:
                                    print(f"Error sending message to {peer}: {e}")
                        


        except KeyboardInterrupt:
            print("\nChatroom closed.")
        finally:
            udp_socket.close()


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


    def connect_to_central_server(self, server_hostname=None, server_port=None):
        '''
        Connects the P2PClient object to the central server.

        args:
            hostname (str): IP address of the central server.
            port (int): Port of the central server.
        '''
        if not server_hostname:
            server_hostname = self.server_hostname
        if not server_port:
            server_port = self.server_port
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5) 
            client_socket.connect((server_hostname, server_port))
            self.address, self.port = client_socket.getsockname()
            return client_socket
        except(socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
            return None

    
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
            self.server_socket = self.connect_to_central_server(self.server_hostname, self.server_port)
            if not self.server_socket:
                print(f"Error creating socket connection to {self.server_hostname}:{self.server_port}")
                return False
            
            join_request = {
                "action": "join",
                "room": room
            }

            self.server_socket.sendall(json.dumps(join_request).encode("utf-8"))
            print(f"Sent join request: {join_request}")

            while True:
                message = self.server_socket.recv(1024)
                if message:
                    response = json.loads(message.decode("utf-8"))

                    if response["status"] == "success":
                        print(f"Client successfully joined {room}")
                        self.room = room
                        self.peers = [tuple(room) for room in response["ips"]]
                        return True
                    
                    else:
                        print(f"Server failed to receive info of {room}")
                        return False

                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        

    def create_room(self, room):
        '''
        Create a room for client-to-client interaction.

        args:
            room (str): Identifier of the room the client wishes to create.
        '''
        print(f"Attempting to create room {room}...")
        try:
            self.server_socket = self.connect_to_central_server(self.server_hostname, self.server_port)
            if not self.server_socket:
                print(f"Error creating socket connection to {self.server_hostname}:{self.server_port}")
                return False
            
            join_request = {
                "action": "create",
                "room": room,
            }
            self.server_socket.sendall(json.dumps(join_request).encode("utf-8"))

            while True:
                message = self.server_socket.recv(1024)
                print(f"Received from central server: {message}")
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


    # fix this for later
    def leave_room(self, room):
        '''
        Get the client to leave the room

        args:
            room (str): Identifier of the room the client wishes to leave.
        '''
        try:
            client_socket = self.connect_to_central_server(self.server_hostname, self.server_port)
            if not client_socket:
                print(f"Error creating socket connection to {self.server_hostname}:{self.server_port}")
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


if __name__ == "__main__":
    target_hostname = "student11.cse.nd.edu"
    target_port = 12345
    client = P2PClient(target_hostname, target_port)