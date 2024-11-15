import socket
import json

def start_server(hostname, port):
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
            # Receive the message from the client
            message = client_socket.recv(4096).decode("utf-8")
            if not message:
                print("No data received. Closing connection.")
                client_socket.close()
                continue

            print(f"Received message from client: {message}")

            # Attempt to parse the message as JSON
            try:
                parsed_message = json.loads(message)
                print(f"Parsed message: {parsed_message}")

                # Check if the message contains the expected keys
                if (
                    parsed_message.get("action") == "join_group" and
                    "group" in parsed_message
                ):
                    group_name = parsed_message["group"]
                    print(f"Client requested to join group: {group_name}")

                    # Respond to the client
                    response = {
                        "status": "success",
                        "message": f"Successfully joined group '{group_name}'"
                    }
                else:
                    # Respond with an error if the message is incorrect
                    response = {
                        "status": "error",
                        "message": "Invalid request format"
                    }
            except json.JSONDecodeError:
                # Respond with an error if the message is not valid JSON
                response = {
                    "status": "error",
                    "message": "Invalid JSON format"
                }

            # Send the response back to the client
            response_message = json.dumps(response)
            client_socket.sendall(response_message.encode("utf-8"))
            print(f"Sent response to client: {response_message}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the connection with the client
            client_socket.close()
            print("Closed connection with client")

if __name__ == "__main__":
    hostname = "0.0.0.0"  # Bind to all interfaces
    port = 12345
    start_server(hostname, port)
