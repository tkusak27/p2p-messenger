from client import P2PClient
import time

target_port = 12345           # specified port
target_hostname = "127.0.0.1"  # localhost


client1 = P2PClient(target_hostname, target_port)
client2 = P2PClient(target_hostname, target_port)

client1.create_room("distsys")
time.sleep(5)
client2.join_room("distsys")
