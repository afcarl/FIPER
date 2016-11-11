import socket
import sys


HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(bytes(data,'UTF-8'))
       
    # Receive data from the server
    received = sock.recv(1024).decode("utf-8") 
except socket.error:
   print ("Network error")

finally:
    sock.close()

print ("Sent:" + data) #.format(data)
print ("Received:" + received)
#print (received)