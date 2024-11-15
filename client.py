import socket
import json

class P2PClient(object):
    def __init__(self):
        pass

    def connect_to_server(self, hostname, port):
        try:
            print(f"Attempting to connect to {hostname}:{port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5) 
            client_socket.connect((hostname, port))
            print(f"Connected to server on {hostname}:{port}")

            join_request = {
                "action": "join",
                "room": "distsys"
            }
            client_socket.sendall(json.dumps(join_request).encode("utf-8"))
            print(f"Sent join request: {join_request}")

            while True:
                message = client_socket.recv(1024)
                if message:
                    print("Received from server:", message.decode("utf-8"))
                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error) as e:
            print(f"Connection failed: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    target_hostname = "127.0.0.1"  # localhost
    target_port = 12345           # specified port
    client = P2PClient()
    client.connect_to_server(target_hostname, target_port)
