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

                    match parsed_message["action"]:

                        case "join":
                            room_name = parsed_message["room"]
                            print(f"{client_address} requested to join room: {room_name}")
                            rooms = self.__add_client_to_room(room_name, client_address)
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

                        case "create":
                            room_name = parsed_message["room"]
                            print(f"{client_address} requested to create room: {room_name}")
                            if room_name:
                                self.__create_room(room_name, client_address)
                                response = {
                                    "status": "success",
                                    "message": f"Successfully created room '{room_name}'",
                                }
                            else:
                                response = {
                                    "status": "error",
                                    "message": "Invalid request format"
                                }

                        case "remove":
                            room_name = parsed_message["room"]
                            print(f"{client_address} requested to leave room ")
                            if room_name:
                                self.__remove_client_from_room(room_name, client_address)
                                response = {
                                    "status": "success",
                                    "message": f"Successfully left room '{room_name}'",
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


    def __create_room(self, room, address):
        '''
        Creates a room by assigning a key in the central server's data structure to the room name (room).
        Adds the client's IP address to be the only member of this room.
        
        args:
            room (str): Identifier of the room the client wishes to create.
            address (str): IP address of the client who requested to create the room.
        '''
        self.rooms[room] = [address]
        return True


    def __add_client_to_room(self, room, address):
        '''
        Adds a client's IP address to a room.

        args:
            room (str): Identifier of the room the client should be added to.
            address (str): IP address of the client who should be added to the room.
        '''
        if room not in self.rooms:
            return False
        
        else:
            self.rooms[room].append(address)
            # self.update_client_list(room)
            return self.rooms[room]
        

    def __remove_client_from_room(self, room, address):
        '''
        Removes a client from a room.

        args:
            room (str): Identifier of the room the client should be removed from.
            address (str): IP address of the client who should be removed from the room.
        '''
        if room not in self.rooms:
            return False
        
        else:
            i = 0
            while i < len(self.rooms[room]):
                if self.rooms[room][i] == address:
                    self.rooms[room].pop(i)
                    return True

        return False                
                

    def __update_client_list(self, room):
        '''
        Re-sends out a client list to all members of a specified room.

        args:
            room (str): Identifier of the room the new list will be send out to.
        '''
        if room not in self.rooms:
            return False


if __name__ == "__main__":
    hostname = "0.0.0.0"
    port = 12345
    nameserver = NameServer()
    nameserver.start_server(hostname, port)
