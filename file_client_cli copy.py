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
        # Cari responsnya, tunggu hingga soket selesai (tidak ada data lagi)
        data_received="" #empty string
        while True:
            # soket tidak menerima semua data sekaligus, data datang sebagian, perlu digabungkan di akhir proses
            data = sock.recv(16)
            if data:
                # data tidak kosong, digabungkan dengan konten sebelumnya
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # tidak ada data lagi, hentikan proses dengan break
                break
        # pada titik ini, data_received (string) akan berisi semua data yang berasal dari soket
        # tUntuk dapat menggunakan data_received sebagai dict, perlu memuatnya menggunakan json.loads()
        # Hapus end marker sebelum mengurai JSON
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
        # proses file dalam bentuk base64 ke bentuk bytes
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
        print("Tes operasi LIST...")
        remote_list()
        
        print("\nTes operasi UPLOAD...")
        # Buat file uji jika belum ada
        test_file = "test_upload.txt"
        if not os.path.exists(test_file):
            with open(test_file, 'w') as f:
                f.write("Ini adalah file uji untuk operasi UPLOAD.")
        remote_upload(test_file)
        
        print("\nTes LIST sesudah Upload...")
        remote_list()
        
        print("\nTes operasi GET...")
        remote_get('test_upload.txt')
        
        print("\nTest operasi DELETE...")
        remote_delete('test_upload.txt')
        
        print("\nTes LIST sesudah Delete...")
        remote_list()
        
    except Exception as e:
        print(f"Error saat testing: {e}")
