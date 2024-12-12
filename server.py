import socket
import json

class NameServer(object):
    def __init__(self):
        '''
        Create a NameServer object.
        '''
        self.rooms = {}

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
                                # Remove room if it's empty
                                if not self.rooms[room_name]:
                                    del self.rooms[room_name]
                                response = {
                                    "status": "success",
                                    "message": f"Successfully left room '{room_name}'"
                                }
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
    hostname = "0.0.0.0"
    port = 12345
    nameserver = NameServer()
    nameserver.start_server(hostname, port)