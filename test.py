from client import P2PClient
import time

target_port = 12345           # specified port
target_hostname = "127.0.0.1"  # localhost


client1 = P2PClient()
client2 = P2PClient()

client1.create_room(target_hostname, target_port, "distsys")
client2.get_room_info(target_hostname, target_port, "distsys")