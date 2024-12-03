import socket
import json

class P2PClient(object):
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.rooms = []

    def connect_to_central_server(self, hostname=None, port=None):
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


    def get_room_info(self, room):
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
                        print(f"Server successfully connected to {room}")
                        self.rooms.append(room)
                        return True
                    
                    else:
                        print(f"Server failed to connect to {room}")
                        return False

                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()


    def create_room(self, room):
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
                        print(f"Server successfully created room {room}")
                        self.rooms.append(room)
                        return True
                    
                    else:
                        print(f"Server failed to create room {room}")
                        return False
        
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()

    def leave_room(self, room):
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
                        self.rooms.append(room)
                        return True
                    
                    else:
                        print(f"Server failed to remove client from room {room}")
                        return False
        
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()


if __name__ == "__main__":
    target_hostname = "127.0.0.1"
    target_port = 12345

