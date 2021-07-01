import argparse
import os
import socket
import Crypto
from Crypto.Util import Padding
from Crypto.Cipher import AES

### Parse possible arguments
parser = argparse.ArgumentParser(description="Parse possible port and key arguments")
parser.add_argument("--port", "-p", type=int, help="Port on which the receiver is listening")
parser.add_argument("--key", "-k", type=str, help="Key for encryptiom")

args = parser.parse_args()
port = args.port
key = args.key

### Set port if None provided
if port is None:
    port = 6000

### Set key if None provided
if key is None:
    ### Set default key
    PRESHARED_KEY = b"a" * 16
else:
    key = key.encode(encoding="utf-8")
    PRESHARED_KEY = key
    if len(key) != 16:
        raise Exception("WrongKeyLength")

def get_local_ip():
    """
    This function determines the IP-address of the receiver
    :return: The current IP-address used in the local network
    """

    ### Connect to Google-DNS server and check the IP
    s = socket.socket()
    s.connect(("8.8.8.8", 443))
    ip = s.getsockname()
    s.close()

    return ip[0]


### Create socket and listen for incoming connections
s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
IP_Receiver = get_local_ip()
s.bind((IP_Receiver, port))
s.listen()
print(f"Receiver listening on [{IP_Receiver}:{port}] ...")

### Accept connection
conn_socket, address = s.accept()

### Get IV
IV = conn_socket.recv(16)
### Get number of files
number_of_files = conn_socket.recv(2)
number_of_files = int.from_bytes(number_of_files, byteorder='big')

### Create new dir for received files
new_dir = "received_files"
if os.path.isdir(new_dir) == False:
    os.mkdir(new_dir)

### Create AES-Cipher
cipher = AES.new(key=PRESHARED_KEY, mode=AES.MODE_CBC, IV=IV)

### Get all files
for _ in range(number_of_files):

    ### Get file-name length: 2 Bytes Big Endian
    file_name_length = conn_socket.recv(2)
    file_name_length = int.from_bytes(file_name_length, byteorder="big")
    ### Assume maximum file-name length of 64 bytes
    file_name = conn_socket.recv(file_name_length).decode(encoding="utf-8")
    print(f"Receiving {file_name}...")

    ### Get file-size: 4 Bytes Big Endian
    file_size = conn_socket.recv(4)
    file_size = int.from_bytes(file_size, byteorder="big")
    ### Get file-data
    file_data = conn_socket.recv(file_size)

    ### Make sure all data is received
    ### Problem with larger files: Possibly not all data received with a single recv()
    while len(file_data) != file_size:
        file_data += conn_socket.recv(file_size-len(file_data))

    ### Decrypt data
    file_data_plaintext = Padding.unpad(cipher.decrypt(file_data), AES.block_size)

    ### Write data to file
    with open(new_dir + os.sep + file_name, "wb") as f:
        f.write(file_data_plaintext)

    print(f"Successfully stored {file_name}\n")

### Close connection and socket
conn_socket.close()
s.close()

print("All files successfully received!")

