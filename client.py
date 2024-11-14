import socket

def scan_ports_and_connect(hostname):
    for port in range(1, 65536):  # Scan all ports from 1 to 65535
        if port in {22, 80, 111, 4330, 6010}: # ports that accept all connections - skip them
            continue
        try:
            print(f"scanning on {hostname}:{port}")
            # Try to connect to the server at the specific port
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1)  # Set a timeout for the connection attempt
            client_socket.connect((hostname, port))
            print(f"Connected to server on {hostname}:{port}")

            # Receive messages from the server
            while True:
                message = client_socket.recv(1024)  # Buffer size 1024
                if message:
                    print("Received from server:", message.decode("utf-8"))
                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error):
            continue  # If connection fails, try the next port

if __name__ == "__main__":
    # Change this to the IP or hostname of the machine running the server
    target_hostname = "127.0.0.1"  # localhost for testing
    scan_ports_and_connect(target_hostname)
