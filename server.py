import socket
import json
import defaultdict

class NameServer(object):
    def __init__(self):
        self.rooms = defaultdict(list)

    def start_server(self, hostname, port):
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

                print(f"Received message from client: {message}")

                try:
                    parsed_message = json.loads(message)
                    print(f"Parsed message: {parsed_message}")

                    if (
                        parsed_message.get("action") == "join_room" and
                        "room" in parsed_message
                    ):
                        room_name = parsed_message["room"]
                        print(f"Client requested to join room: {room_name}")

                        rooms = self.add_client_to_room(room_name, client_address)
                        
                        if rooms:
                            response = {
                                "status": "success",
                                "message": f"Successfully joined room '{room_name}'",
                                "ips": rooms,
                            }
                        else:
                            response = {
                                "status": "failure",
                                "message": f"room {room_name} does not exist"
                            }
                    else:
                        response = {
                            "status": "error",
                            "message": "Invalid request format"
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

    def add_client_to_room(self, room, address):
        if room not in self.rooms:
            return False
        
        else:
            self.rooms[room].append(address)
            self.update_client_list(room)
            return self.rooms[room]
        
    def update_client_list(room):
        # need to implement
        pass

        

if __name__ == "__main__":
    hostname = "0.0.0.0"
    port = 12345
    nameserver = NameServer()
    nameserver.start_server(hostname, port)
