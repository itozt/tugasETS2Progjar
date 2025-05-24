import socket
import json
import base64
import logging
import os

server_address=('172.16.16.101',46666)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                #data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        # Remove end marker before parsing JSON
        data_received = data_received.replace("\r\n\r\n", "")
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving:{e}")
        return False


def remote_list():
    command_str= "LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str=f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        #proses file dalam bentuk base64 ke bentuk bytes
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filename=""):
    if not os.path.exists(filename):
        print(f"File {filename} tidak ditemukan")
        return False

    try:
        with open(filename, 'rb') as fp:
            isifile = base64.b64encode(fp.read()).decode()
        base_filename = os.path.basename(filename)
        command_str = f'UPLOAD {base_filename} "{isifile}"'
        hasil = send_command(command_str)
        if (hasil['status'] == 'OK'):
            print(f"File {hasil['data_namafile']} berhasil diupload")
            return True
        else:
            print("Gagal upload")
            return False
    except Exception as e:
        print(f"Gagal upload: {e}")
        return False

def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print(f"File {hasil['data_namafile']} berhasil didelete")
        return True
    else:
        print("Gagal")
        return False

if __name__=='__main__':
    server_address=('172.16.16.101',46666)
    print(f"Connecting to server at {server_address}")
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        print("Testing LIST operation...")
        remote_list()
        
        print("\nTesting UPLOAD operation...")
        # Create a test file if it doesn't exist
        test_file = "test_upload.txt"
        if not os.path.exists(test_file):
            with open(test_file, 'w') as f:
                f.write("This is a test file for upload operation.")
        remote_upload(test_file)
        
        print("\nTesting LIST after upload...")
        remote_list()
        
        print("\nTesting GET operation...")
        remote_get('test_upload.txt')
        
        print("\nTesting DELETE operation...")
        remote_delete('test_upload.txt')
        
        print("\nTesting LIST after delete...")
        remote_list()
        
    except Exception as e:
        print(f"Error during testing: {e}")
