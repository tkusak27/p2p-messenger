import socket
import json
import time
import os
from datetime import datetime

class NameServer(object):
    def __init__(self):
        '''
        Create a NameServer object with logging capabilities.
        '''
        self.rooms = {}
        self.log_file = "server_log.json"
        self.load_state()

    def log_state(self):
        '''
        Log the current state of rooms to a JSON file with timestamp.
        '''
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rooms": self.rooms
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Error writing to log: {e}")

    def load_state(self):
        '''
        Load the most recent state from the log file and verify rooms.
        '''
        if not os.path.exists(self.log_file):
            print("No previous state found.")
            return

        try:
            # Read the last line of the log file
            with open(self.log_file, 'r') as f:
                last_line = None
                for line in f:
                    if line.strip():
                        last_line = line
                
                if last_line:
                    state = json.loads(last_line)
                    stored_rooms = state.get("rooms", {})
                    
                    # Try to verify each room with all its clients
                    for room_name, clients in stored_rooms.items():
                        if clients:
                            if self.verify_room(room_name, clients):
                                print(f"Successfully recovered room: {room_name}")
                            else:
                                print(f"Room {room_name} is no longer active")
                        else:
                            print(f"Room {room_name} had no clients - removing")
                            if room_name in self.rooms:
                                del self.rooms[room_name]

        except Exception as e:
            print(f"Error loading state: {e}")

    def verify_room(self, room_name, clients):
        '''
        Verify a room's existence by trying to contact each client until one responds.
        
        args:
            room_name (str): Name of the room to verify
            clients (list): List of (address, port) tuples for all clients in the room
        '''
        try:
            # Create UDP socket for verification
            verify_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            verify_socket.settimeout(2)  # Short timeout for each attempt

            # Try each client until we get a response
            for client in clients:
                try:
                    # Send verification request
                    verify_msg = {
                        "type": "room_verify",
                        "room": room_name
                    }
                    verify_socket.sendto(json.dumps(verify_msg).encode('utf-8'), tuple(client))

                    # Wait for response
                    data, _ = verify_socket.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    
                    if response.get("type") == "room_verify_response" and response.get("room") == room_name:
                        # Update room with latest peer list
                        if "active_clients" in response:
                            self.rooms[room_name] = response["active_clients"]
                            print(f"Updated room {room_name} with current peer list")
                            return True

                except socket.timeout:
                    print(f"No response from client {client} in room {room_name}")
                    continue
                except Exception as e:
                    print(f"Error verifying with client {client}: {e}")
                    continue

            # If we get here, no clients responded
            print(f"No clients responded in room {room_name} - closing room")
            if room_name in self.rooms:
                del self.rooms[room_name]
            return False

        except Exception as e:
            print(f"Error in room verification: {e}")
            return False
        finally:
            verify_socket.close()

    def start_server(self, hostname, port):
        '''
        Starts the server.

        args:
            hostname (str): The IP address of the central server that stores room information.
            port (int): The port where the central server is running. 
        '''
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((hostname, port))
        server_socket.listen(1)
        print(f"Server listening on {hostname}:{port}")

        while True:
            print("Waiting for a connection...")
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            
            try:
                message = client_socket.recv(4096).decode("utf-8")
                if not message:
                    print("No data received. Closing connection.")
                    client_socket.close()
                    continue

                try:
                    parsed_message = json.loads(message)
                    print(f"Parsed message: {parsed_message}")
                    action = parsed_message["action"]

                    if action == "list":
                        print(f"{client_address} requested to list rooms")
                        if self.rooms:
                            response = {
                                "status": "success",
                                "message": "Retrieved available rooms",
                                "rooms": {
                                    room_name: {
                                        "member_count": len(members)
                                    }
                                    for room_name, members in self.rooms.items()
                                }
                            }
                        else:
                            response = {
                                "status": "success",
                                "message": "There are no active rooms available"
                            }

                    elif action == "join":
                        room_name = parsed_message["room"]
                        print(f"{client_address} requested to join room: {room_name}")
                        if room_name in self.rooms:
                            self.rooms[room_name].append(client_address)
                            response = {
                                "status": "success",
                                "message": f"Successfully joined room '{room_name}'",
                                "ips": self.rooms[room_name]
                            }
                            self.log_state()  # Log after join
                        else:
                            response = {
                                "status": "failure",
                                "message": f"Room {room_name} does not exist"
                            }

                    elif action == "create":
                        room_name = parsed_message["room"]
                        print(f"{client_address} requested to create room: {room_name}")
                        if room_name:
                            self.rooms[room_name] = [client_address]
                            response = {
                                "status": "success",
                                "message": f"Successfully created room '{room_name}'"
                            }
                            self.log_state()  # Log after creation
                        else:
                            response = {
                                "status": "error",
                                "message": "Invalid request format"
                            }

                    elif action == "update_room":
                        room_name = parsed_message["room"]
                        active_clients = parsed_message["active_clients"]
                        print(f"{client_address} sent updated client list for room: {room_name}")
                        
                        if room_name in self.rooms:
                            self.rooms[room_name] = [tuple(client) for client in active_clients]
                            if not self.rooms[room_name]:
                                del self.rooms[room_name]
                            response = {
                                "status": "success",
                                "message": f"Successfully updated room '{room_name}'"
                            }
                            self.log_state()  # Log after update
                        else:
                            response = {
                                "status": "error",
                                "message": f"Room {room_name} does not exist"
                            }

                    elif action == "leave":
                        room_name = parsed_message["room"]
                        original_address = parsed_message["original_address"]
                        original_port = parsed_message["original_port"]
                        original_client = (original_address, original_port)
                        print(f"Client {original_client} requested to leave room {room_name}")
                        
                        if room_name in self.rooms:
                            if original_client in self.rooms[room_name]:
                                self.rooms[room_name].remove(original_client)
                                if not self.rooms[room_name]:
                                    del self.rooms[room_name]
                                response = {
                                    "status": "success",
                                    "message": f"Successfully left room '{room_name}'"
                                }
                                self.log_state()  # Log after leave
                            else:
                                response = {
                                    "status": "error",
                                    "message": f"Client {original_client} not found in room {room_name}"
                                }
                        else:
                            response = {
                                "status": "error",
                                "message": f"Room {room_name} does not exist"
                            }

                except json.JSONDecodeError:
                    response = {
                        "status": "error",
                        "message": "Invalid JSON format"
                    }

                response_message = json.dumps(response)
                client_socket.sendall(response_message.encode("utf-8"))
                print(f"Sent response to client: {response_message}")

            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                client_socket.close()
                print("Closed connection with client")

if __name__ == "__main__":
    hostname = "127.0.0.1"
    port = 12345
    nameserver = NameServer()
    nameserver.start_server(hostname, port)