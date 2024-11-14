import socket
import time

def start_server(hostname, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((hostname, port))
    server_socket.listen(1)
    print(f"Server listening on {hostname}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        
        # Send message every minute
        while True:
            message = "Hello from the server!"
            client_socket.send(bytes(message, "utf-8"))
            print("Sent message to client")
            time.sleep(1)  # Send message every 1 seconds

if __name__ == "__main__":
    # Change this to your desired hostname and port
    hostname = "0.0.0.0"  # Listening on just localhost
    port = 12345  # Choose an arbitrary port
    start_server(hostname, port)
