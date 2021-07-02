import socket
import tkinter
from tkinter import filedialog
import argparse
import Crypto
from Crypto.Cipher import AES
from Crypto.Util import Padding
import os


### Parse Arguments: IP-address or name of receiver and respective port
parser = argparse.ArgumentParser(description="Get receiver-name/address and port")

parser.add_argument("--address", "-a", type=str, help="IP-address of reveiver")
parser.add_argument("--name", "-n", type=str, help="Hostname of reveiver")
parser.add_argument("--port", "-p", type=int, help="Port on which reveiver is listening")
parser.add_argument("--key", "-k", type=str, help="Key for encryption")

args = parser.parse_args()

receiver_address = args.address
receiver_name = args.name
receiver_port = args.port
key = args.key


### Get IP-address by name...
if receiver_name is not None:
    receiver_ip = socket.gethostbyname(receiver_name)
### ... or directly set the IP-address if available
elif receiver_address is not None:
    receiver_ip = receiver_address
else:
    raise Exception("NoIPprovided")

### Get port
if receiver_port is None:
    receiver_port = 6000

### Get key
if key is None:
    ### Set default key
    PRESHARED_KEY = b"a" * 16
else:
    key = key.encode(encoding="utf-8")
    PRESHARED_KEY = key
    if len(key) != 16:
        raise Exception("WrongKeyLength")


### Select files to transfer
root = tkinter.Tk()
filenames = filedialog.askopenfilenames()
root.destroy()

### Create AES-cipher
cipher = AES.new(PRESHARED_KEY, AES.MODE_CBC)

DATA = list()

for file in filenames:

    ### Get file data
    with open(file, "rb") as f:
        file_data_plaintext = f.read()

    ### Encrypt file data
    file_data_ciphertext = cipher.encrypt(Padding.pad(file_data_plaintext, AES.block_size))

    ### Get file size in 4-Byte Big Endian Format
    ### Important: Determine the file-size after padding and encryption
    file_size_padding = len(file_data_ciphertext)
    file_size = file_size_padding.to_bytes(length=4, byteorder="big")


    ### Get file base name
    file_name = bytes(os.path.basename(file), encoding="utf-8")

    DATA.append((file_name, file_size, file_data_ciphertext))


### Get initialization vector (needed for decryption)
IV = cipher.iv
### Get number of files
number_of_files = len(filenames).to_bytes(length=2, byteorder='big')


### Create socket and connect to receiver
sender_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
sender_socket.connect((receiver_ip, receiver_port))

print(f"Connected to [{receiver_ip}:{receiver_port}]")

### Send IV and the number of files
sender_socket.send(IV)
sender_socket.send(number_of_files)

### Go over all files and send the data
for file in DATA:

    ### Send file-name length
    file_name_length = len(file[0]).to_bytes(length=2, byteorder="big")
    sender_socket.send(file_name_length)
    ### Send file-name
    sender_socket.send(file[0])
    ### Send file-size
    sender_socket.send(file[1])
    ### Send file-data
    sender_socket.send(file[2])
    
    print(f"Sent {file[0].decode(encoding='utf-8')} ...\n")

### Close socket when finished
sender_socket.close()

print("Files sent successfully!")
