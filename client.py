import socket, json, sys, select, time
from styles.bcolors import bcolors
from collections import deque

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
        self.tcp_address = None
        self.tcp_port = None
        self.user_id = None
        self.message_log = deque(maxlen=20)
        self.message_clock = dict()
        self.join_time_clock = {}  # Track clock values at join time
        self.recovery_in_progress = set()
        self.received_messages = set()

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
        print(bcolors.OKGREEN + bcolors.BOLD + "StudyChat P2P client has been started!\n" + bcolors.ENDC) 
        print(bcolors.YELLOW + "To get started, please create a username: " + bcolors.ENDC, end="", flush=True)
        self.user_id = sys.stdin.readline().strip()
        
        while True:
            print("\nNow select one of the options below by typing the corresponding letter and pressing enter.")
            user_input = self.display_menu()

            # used to be match statement but wasn't working
            # list public rooms
            if user_input == "A":
                self.list_rooms()

            # join a room
            if user_input == "B":
                out = self.join_handler()
                if out: 
                    self.running = True
                    self.chat_handler()

            # create a room
            elif user_input == "C":
                print(bcolors.YELLOW + "Please enter the name of the room you wish to create: " + bcolors.ENDC, end="", flush=True)
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
        print("\nPlease enter the name of the room you wish to join.\nInput: ", end="", flush=True)

        room_name = sys.stdin.readline().strip()
        return self.join_room(room_name)
    

    def chat_handler(self):
        '''
        Key handler which handles all chat communication, including peer updates
        '''
        print(f"{bcolors.GREEN}{bcolors.BOLD}Chatroom {self.room} opened!{bcolors.ENDC}")
        print(f"{bcolors.CYAN}{len(self.peers)} peers are here now.{bcolors.ENDC}")
        print(bcolors.RED + "Type '/help' for a list of helpful commands to navigate the application." + bcolors.ENDC)
        print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

        self.running = True

        # Create the single UDP socket that will be used throughout the session
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.port))

        try:
            # Broadcast join message to all peers using the single UDP socket
            join_msg = {
                "status": "update",
                "type": "join",
                "room": self.room,
                "member": self.user_id,
                "address": self.address,
                "port": self.port
            }
            
            for peer in self.peers:
                try:
                    udp_socket.sendto(json.dumps(join_msg).encode('utf-8'), peer)
                except Exception as e:
                    print(f"Error announcing join to peer {peer}: {e}")

            while self.running:
                readable, _, _ = select.select([sys.stdin, udp_socket], [], [])

                for source in readable:
                    if source == udp_socket:
                        data, addr = udp_socket.recvfrom(1024)
                        msg = json.loads(data.decode('utf-8'))
                        
                        if "status" in msg and msg["status"] == "update":
                            if "type" in msg and msg["type"] == "join":
                                # Add the new peer to our list
                                new_peer = (msg["address"], msg["port"])
                                if new_peer not in self.peers:
                                    self.peers.append(new_peer)
                                print(f"{bcolors.WARNING}{msg['member']} has joined the room{bcolors.ENDC}")
                                
                            elif "type" in msg and msg["type"] == "leave":
                                # Remove the peer that's leaving
                                leaving_peer = (msg["address"], msg["port"])
                                if leaving_peer in self.peers:
                                    self.peers.remove(leaving_peer)
                                # Also remove from clocks
                                leaving_port = str(msg["port"])
                                if leaving_port in self.message_clock:
                                    del self.message_clock[leaving_port]
                                if leaving_port in self.join_time_clock:
                                    del self.join_time_clock[leaving_port]
                                if leaving_port in self.recovery_in_progress:
                                    self.recovery_in_progress.remove(leaving_port)
                                print(f"{bcolors.WARNING}{msg['member']} has left the room{bcolors.ENDC}")
                            print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

                        elif msg.get("type") == "message_request":
                            self.send_requested_messages(
                                udp_socket, 
                                msg["requesting_port"], 
                                msg["count"],
                                msg.get("from_count", 0)
                            )

                        elif msg.get("type") == "recovery":
                            sender_port = str(addr[1])
                            msg_id = msg["message_id"]
                            
                            if msg_id not in self.received_messages:
                                self.received_messages.add(msg_id)
                                sequence_number = msg["sequence_number"]
                                
                                # Only process if this is the next message we're expecting
                                if sequence_number == self.message_clock.get(sender_port, 0) + 1:
                                    self.message_clock[sender_port] = sequence_number
                                    print(f'\n{bcolors.YELLOW}[RECOVERY] {msg["user"]}: {msg["body"]}{bcolors.ENDC}')
                                    print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

                        elif msg.get("type") == "recovery_complete":
                            sender_port = msg["sender_port"]
                            if sender_port in self.recovery_in_progress:
                                self.recovery_in_progress.remove(sender_port)
                                self.message_clock.update(msg["final_clock"])
                                print(f"\n{bcolors.YELLOW}[RECOVERY] Completed recovery from client {sender_port}{bcolors.ENDC}")
                                print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

                        else:  # Regular chat message
                            sender_port = str(addr[1])
                            msg_id = msg.get("message_id", f"{sender_port}_{time.time()}")
                            
                            if msg_id not in self.received_messages:
                                self.received_messages.add(msg_id)
                                
                                # Check for clock inconsistencies
                                if "message_clock" in msg:
                                    received_clock = msg["message_clock"]
                                    needs_recovery = False
                                    
                                    # Only check clocks if we're not already recovering
                                    if not self.recovery_in_progress:
                                        for port, count in received_clock.items():
                                            if port == sender_port:
                                                # Only recover if we've seen messages from this client before
                                                if port in self.join_time_clock:
                                                    expected = self.message_clock.get(port, 0) + 1
                                                    join_time_count = self.join_time_clock.get(port, 0)
                                                    # Only recover if messages were lost after we joined
                                                    if count > expected and count > join_time_count:
                                                        needs_recovery = True
                                            else:
                                                local_count = self.message_clock.get(port, 0)
                                                join_time_count = self.join_time_clock.get(port, 0)
                                                # Only recover if messages were lost after we joined
                                                if count > local_count and count > join_time_count:
                                                    needs_recovery = True
                                        
                                        if needs_recovery:
                                            self.request_missing_messages(
                                                udp_socket, 
                                                sender_port, 
                                                received_clock[sender_port],
                                                self.message_clock.get(sender_port, 0)
                                            )
                                    
                                    # Update clock if message is in sequence or from new client
                                    if not needs_recovery:
                                        self.message_clock.update(received_clock)
                                
                                if msg.get("type") != "recovery":
                                    print(f'\n{msg["user"]}: {msg["body"]}')
                                    print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

                    elif source == sys.stdin: 
                        output = self.handle_user_input(udp_socket)
                        if output == -1:
                            # Handle leaving the room with the same socket
                            if self.room:
                                self.leave_room(self.room, udp_socket)
                            break
        except KeyboardInterrupt:
            print("\nChatroom closed.")
        finally:
            udp_socket.close()

    def request_missing_messages(self, udp_socket, peer_port, expected_count, current_count):
        '''
        Request missing messages from a peer when clock inconsistency is detected.
        '''
        # Don't request if already in progress for this peer
        if peer_port in self.recovery_in_progress:
            return
            
        missing_count = expected_count - current_count
        request_msg = {
            "type": "message_request",
            "requesting_port": str(self.port),
            "count": missing_count,
            "from_count": current_count  # Add starting point for recovery
        }
        
        peer_address = None
        for peer in self.peers:
            if str(peer[1]) == peer_port:
                peer_address = peer
                break
        
        if peer_address:
            self.recovery_in_progress.add(peer_port)
            json_request = json.dumps(request_msg)
            udp_socket.sendto(json_request.encode('utf-8'), peer_address)

    def send_requested_messages(self, udp_socket, requesting_port, count, from_count):
        '''
        Send requested messages from our log to the requesting peer.
        
        args:
            udp_socket (socket): The UDP socket for sending messages
            requesting_port (str): Port of the requesting peer
            count (int): Number of messages requested
            from_count (int): Starting message count to sync from
        '''
        # Find the messages that were sent after from_count
        messages_to_send = []
        current_messages = list(self.message_log)
        current_count = self.message_clock[str(self.port)]
        start_index = max(0, len(current_messages) - (current_count - from_count))
        
        if start_index < len(current_messages):
            messages_to_send = current_messages[start_index:]

        requester_address = None
        for peer in self.peers:
            if str(peer[1]) == requesting_port:
                requester_address = peer
                break
        
        if requester_address:
            for idx, message in enumerate(messages_to_send):
                msg_id = f"{self.port}_{from_count + idx + 1}"
                send_msg = {
                    "user": self.user_id,
                    "body": message,
                    "message_clock": self.message_clock.copy(),
                    "type": "recovery",
                    "message_id": msg_id,
                    "sequence_number": from_count + idx + 1
                }
                json_send_msg = json.dumps(send_msg)
                udp_socket.sendto(json_send_msg.encode('utf-8'), requester_address)
            
            # Send end of recovery message
            end_msg = {
                "type": "recovery_complete",
                "final_clock": self.message_clock.copy(),
                "sender_port": str(self.port)
            }
            udp_socket.sendto(json.dumps(end_msg).encode('utf-8'), requester_address)

    
    def handle_user_input(self, udp_socket):
        '''
        Method that handles user input, such as:
            1. Sending a chat to all peers
            2. Handling special user input (commands)
            3. Exiting the chatroom if necessary

        args:
            udp_socket (socket): The UDP socket the client is listening on.
        '''
        message = sys.stdin.readline().strip()
        
        # special user command
        if message.lower().startswith("/"):
            if message.lower() == "/help":
                print("\n=== Options ===\n")
                print("/clock - shows clock of messages sent by each client")
                print("/history - shows most recent sent messages")
                print("/peers - shows current peers in client list")
                print("/exit - exits room and returns to menu")
                print("\n====================\n")

            elif message.lower() == "/exit":
                print("Exiting chatroom...")
                if self.room:
                    self.leave_room(self.room, udp_socket=udp_socket)
                self.running = False
                return -1
            
            elif message.lower() == "/history":
                print("\n=== Message History ===")
                for idx, msg in enumerate(self.message_log, 1):
                    print(f"{idx}. {msg}")
                print("====================\n")

            elif message.lower() == "/clock":
                print("\n=== Message Clock ===")
                for port, count in self.message_clock.items():
                    print(f"Client {port}: {count} messages")
                print("====================\n")

            elif message.lower() == "/peers":
                print("\n=== Peers ===")
                for peer in self.peers:
                    print(f"{peer}")
                print("====================\n")

        
        print(bcolors.CYAN + bcolors.BOLD + "> " + bcolors.ENDC, end="", flush=True)

        # Only add non-command messages to the log and update clock
        if not message.startswith("/"):
            self.message_log.append(message)
            self.message_clock[str(self.port)] = self.message_clock.get(str(self.port), 0) + 1

            for peer in self.peers:
                if peer != (self.address, self.port):
                    try:
                        send_msg = {
                            "user": self.user_id,
                            "body": message,
                            "message_clock": self.message_clock,
                            "type": "chat"
                        }
                        json_send_msg = json.dumps(send_msg)
                        udp_socket.sendto(json_send_msg.encode('utf-8'), tuple(peer))

                    except Exception as e:
                        print(f"Error sending message to {peer}: {e}")


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

    def list_rooms(self):
        '''
        Lists all available rooms from the central server.
        
        Returns:
            bool: True if rooms were successfully listed, False otherwise
        '''
        try:
            self.server_socket = self.connect_to_central_server(self.server_hostname, self.server_port)
            if not self.server_socket:
                print(f"Error creating socket connection to {self.server_hostname}:{self.server_port}")
                return False
            
            list_request = {
                "action": "list"
            }
            
            self.server_socket.sendall(json.dumps(list_request).encode("utf-8"))
            
            message = self.server_socket.recv(1024)
            if message:
                response = json.loads(message.decode("utf-8"))
                
                if response["status"] == "success":
                    rooms = response.get("rooms", {})
                    if not rooms:
                        print(f"\n{bcolors.YELLOW}No active rooms available.{bcolors.ENDC}")
                    else:
                        print(f"\n{bcolors.GREEN}Available rooms:{bcolors.ENDC}")
                        for room_name, info in rooms.items():
                            member_count = info.get("member_count", 0)
                            print(f"{bcolors.CYAN}• {room_name}: {member_count} member(s){bcolors.ENDC}")
                    return True
                else:
                    print(f"{bcolors.RED}Failed to retrieve room list: {response.get('message', 'Unknown error')}{bcolors.ENDC}")
                    return False
                    
        except (socket.timeout, socket.error) as e:
            print(f"{bcolors.RED}Connection failed: {e}{bcolors.ENDC}")
            return False
        finally:
            if self.server_socket:
                self.server_socket.close()

    def join_room(self, room):
        '''
        Joins a specified room by getting initial peer list from server then broadcasting presence.
        
        args:
            room (str): Identifier of the room the client wishes to join.
        '''
        try:
            # First get initial room info from server
            self.server_socket = self.connect_to_central_server(self.server_hostname, self.server_port)
            if not self.server_socket:
                print(f"Error creating socket connection to {self.server_hostname}:{self.server_port}")
                return False
            
            # Store TCP connection details when joining
            self.tcp_address, self.tcp_port = self.server_socket.getsockname()
            
            join_request = {
                "action": "join",
                "room": room
            }

            self.server_socket.sendall(json.dumps(join_request).encode("utf-8"))

            message = self.server_socket.recv(1024)
            if message:
                response = json.loads(message.decode("utf-8"))

                if response["status"] == "success":
                    print(f"Got initial room info for {room}")
                    self.room = room
                    self.peers = [tuple(peer) for peer in response["ips"]]
                    
                    # Initialize message tracking
                    self.message_clock = {}
                    self.join_time_clock = {}
                    if str(self.port) not in self.message_clock:
                        self.message_clock[str(self.port)] = 0
                        self.join_time_clock[str(self.port)] = 0
                        
                    return True
                else:
                    print(f"Server failed to provide room info for {room}")
                    return False

        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
            return False
        

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
            
            # Store TCP connection details when creating
            self.tcp_address, self.tcp_port = self.server_socket.getsockname()
            
            join_request = {
                "action": "create",
                "room": room,
            }
            self.server_socket.sendall(json.dumps(join_request).encode("utf-8"))

            message = self.server_socket.recv(1024)
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


    def leave_room(self, room, udp_socket):
        '''
        Leave a room and notify peers directly.
        
        args:
            room (str): Identifier of the room to leave
            udp_socket (socket): The UDP socket for sending the leave notification
        '''
        try:
            # Prepare leave notification
            leave_notification = {
                "status": "update",
                "type": "leave",
                "room": room,
                "member": self.user_id,
                "address": self.address,
                "port": self.port
            }
            
            # Notify all peers using the provided socket
            for peer in self.peers:
                if peer != (self.address, self.port):
                    try:
                        json_notification = json.dumps(leave_notification)
                        udp_socket.sendto(json_notification.encode('utf-8'), peer)
                    except Exception as e:
                        print(f"Error notifying peer {peer} of leave: {e}")

            # Then notify server with original connection details
            client_socket = self.connect_to_central_server()
            if client_socket:
                try:
                    leave_request = {
                        "action": "leave",
                        "room": room,
                        "original_address": self.tcp_address,
                        "original_port": self.tcp_port
                    }
                    client_socket.sendall(json.dumps(leave_request).encode("utf-8"))
                    # Wait for server response
                    response = json.loads(client_socket.recv(1024).decode("utf-8"))
                    if response["status"] != "success":
                        print(f"Server failed to process leave request: {response.get('message', 'Unknown error')}")
                finally:
                    client_socket.close()

            # Clear local state
            print(f"Left room {room}")
            self.room = None
            self.peers = []
            self.message_log.clear()
            self.message_clock.clear()
            self.join_time_clock.clear()
            self.recovery_in_progress.clear()
            self.received_messages.clear()
            return True
                
        except Exception as e:
            print(f"Error during room exit: {e}")
            return False

if __name__ == "__main__":
    target_hostname = "student13.cse.nd.edu"
    target_port = 12345
    client = P2PClient(target_hostname, target_port)