import socket
import json

class NameServer(object):
    def __init__(self):
        # need to load in checkpoint and logs
        pass

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
                        parsed_message.get("action") == "join_group" and
                        "group" in parsed_message
                    ):
                        group_name = parsed_message["group"]
                        print(f"Client requested to join group: {group_name}")

                        response = {
                            "status": "success",
                            "message": f"Successfully joined group '{group_name}'"
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

if __name__ == "__main__":
    hostname = "0.0.0.0"
    port = 12345
    nameserver = NameServer()
    nameserver.start_server(hostname, port)
