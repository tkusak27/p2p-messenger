from client import P2PClient
import time

target_port = 12345
target_hostname = "student13.cse.nd.edu"


client1 = P2PClient(target_hostname, target_port)

client1.create_room("distsys")
