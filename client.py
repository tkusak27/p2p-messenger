import socket

def scan_ports_and_connect(hostname):
    for port in range(1, 65536): 
        if port in {22, 80, 111, 4330, 6010}: # ports that accept all connections - skip them
            continue
        try:
            print(f"scanning on {hostname}:{port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1) 
            client_socket.connect((hostname, port))
            print(f"Connected to server on {hostname}:{port}")

            while True:
                message = client_socket.recv(1024)
                if message:
                    print("Received from server:", message.decode("utf-8"))
                else:
                    print("Server closed the connection.")
                    break
        except (socket.timeout, socket.error):
            continue

if __name__ == "__main__":
    target_hostname = "127.0.0.1"  # localhost for testing
    scan_ports_and_connect(target_hostname)
