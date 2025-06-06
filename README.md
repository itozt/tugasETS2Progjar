# Tugas ETS Pemrograman Jaringan
## Daftar Isi
- [Soal](https://github.com/itozt/tugasETSProgjar/tree/main#-soal)
- [Kegunaan Masing-Masing File](https://github.com/itozt/tugasETSProgjar/tree/main#-kegunaan-masing-masing-file)
- [Alur Kerja / Arsitektur](https://github.com/itozt/tugasETSProgjar/tree/main#-alur-kerja--arsitektur)
- [Alur Kerja / Arsitektur (Secara Singkat)](https://github.com/itozt/tugasETSProgjar/tree/main#-alur-kerja--arsitektur-secara-singkat)
- [Diagram Arsitektur Alur Kerja](https://github.com/itozt/tugasETSProgjar/tree/main#-diagram-arsitektur-alur-kerja)
- Penjelasan Tiap Class File
  - [file_interface.py](https://github.com/itozt/tugasETSProgjar/tree/main#-file_interfacepy)
  - [file_thread_pool.py](https://github.com/itozt/tugasETSProgjar/tree/main#-file_thread_poolpy)
  - [file_client_cli.py](https://github.com/itozt/tugasETSProgjar/tree/main#-file_client_clipy)
  - [file_client_stress_test.py](https://github.com/itozt/tugasETSProgjar/tree/main#-file_client_stress_testpy)
  - [run_for_test.py]()
- [Cara Pengerjaan](https://github.com/itozt/tugasETSProgjar/tree/main#-cara-pengerjaan)

## 🌳 Soal
Dari hasil modifikasi program [https://github.com/rm77/progjar/tree/master/progjar4a](https://github.com/rm77/progjar/tree/master/progjar4a) pada TUGAS 3 <br>

Rubahlah model pemrosesan concurrency yang ada, dari multithreading menjadi: 
  - Multihreading menggunakan pool<br>
  - Multiprocessing menggunakan pool <br>

Modifikasilah program client untuk melakukan:
- Download file
- Upload file
- List file <br>

Lakukan stress test pada program server tersebut dengan cara membuat client agar melakukan proses pada nomor 3 secara concurrent dengan menggunakan multithreading pool dan multiprocessing pool <br>

Kombinasi stress test: <br>
- Operasi download, upload
- Volume file 10 MB, 50 MB, 100 MB
- Jumlah client worker pool 1, 5, 50
- Jumlah server worker pool 1, 5, 50 <br>

Untuk setiap kombinasi tersebut catatlah:
- Waktu total per client melakukan proses upload/download (dalam seconds)
- Throughput per client (dalam bytes per second, total bytes yang sukses diproses per second)
- Jumlah worker client yang sukses dan gagal (jika sukses semua, maka gagal = 0)
- Jumlah worker server yang sukses dan gagal (jika sukses semua, maka gagal = 0) <br>

Hasil stress test, harus direkap ke sebuah tabel yang barisnya adalah total kombinasi dari nomor 4. Total baris kombinasi = 2x3x3x3 = 54 baris, dengan kolom: <br>
- Nomor
- Operasi
- Volume
- Jumlah client worker pool
- Jumlah server worker pool
- Waktu total per client
- Throughput per client
- Jumlah worker client yang sukses dan gagal
- Jumlah worker server yang sukses dan gagal

## 🌳 Kegunaan Masing-Masing File
Untuk menjalankan stress test, saya memerlukan beberapa file class. Berikut merupakan kegunaan dari masing-masing fiel class : 
- <p align="justify"><b>file_protocol.py</b> : Menerjemahkan string perintah (LIST/GET/UPLOAD/DELETE) dari klien menjadi pemanggilan API di FileInterface. </p>
- <p align="justify"><b>file_interface.py</b> : Implementasi operasi file-level di direktori `files/` yaitu operasi GET, UPLOAD, dan LIST.
- **file_server.py** : Dua mode server :
  - LegacyServer — model threading satu-per-klien <br>
  - PoolServer — model multithreading atau multiprocessing dengan pool worker<br>
  Menerima koneksi socket, men‐dispatch ke worker, mencatat statistik (aktif/sukses/gagal/total)</p>
- <p align="justify"><b>file_thread_pool.py</b> : Varian server khusus “ThreadPoolServer” (mirip PoolServer), hanya pool saja (tidak ada legacy). Tambahan metode get_worker_stats() untuk monitoring di runtime.</p>
- <p align="justify"><b>file_client_cli.py</b> : Klien interaktif CLI untuk manual testing : `remote_list(), remote_get(), remote_upload(), remote_delete()` Berkomunikasi via socket, decode/encode JSON & Base64, menampilkan hasil ke layar.</p>
- **file_client_stress_test.py** : Klien otomatisasi stress‐test: 
  - Membangkitkan file uji ukuran 10/50/100 MB
  - Menjalankan operasi upload/download/LIST secara concurrent (thread vs process pool)
  - Mengukur durasi, throughput, sukses/gagal per worker
  - Menyimpan ringkasan hasil ke CSV dan menampilkan di console.
- **run_for_test.py** : Skrip orchestration untuk:
  1. Memulai server (file_thread_pool.py) dengan berbagai konfigurasi worker & mode (threading/processing)
  2. Menjalankan klien stress‐test (file_client_stress_test.py) terhadap server yang sedang berjalan
  3. Menghentikan server, lalu pindah ke konfigurasi berikutnya
  4. Menyajikan ringkasan hasil per konfigurasi.

## 🌳 Alur Kerja / Arsitektur
1. **Inisialisasi TestRunner** <br>
   `run_for_test.py` mem-parsing argumen, lalu membuat objek TestRunner.
2. **Loop Konfigurasi Server** <br>
   TestRunner memiliki daftar konfigurasi:
   ``` graphql
   [
   (1, False, "1worker_threading"),
   (5, False, "5workers_threading"),
   (50, False, "50workers_threading"),
   (1, True, "1worker_multiprocessing"),
   (5, True, "5workers_multiprocessing"),
   (50, True, "50workers_multiprocessing"),
   ]
   ```
   Untuk tiap tuple `(server_workers, use_mp, description)`
3. **Start Server** <br>
   - Panggil `start_server(port=46666, workers=server_workers, use_multiprocessing=use_mp)`
   - Internally, ini menjalankan:
     ``` css
     python thread_pool.py --port 46666 --workers {server_workers} [--multiprocessing]
     ```
   - thread_pool.py (alias file_thread_pool.py) membuat instance ThreadPoolServer:
     - Buka socket TCP pada port 46666
     - Buat ThreadPoolExecutor atau ProcessPoolExecutor dengan `max_workers=server_workers`
     - Siap menerima koneksi client
4. **Run Stress Test Client**
   - Jika server berhasil start, TestRunner memanggil run_stress_test(server_workers=[server_workers], client_multiprocessing=False, output_prefix="{description}_")
   - Ini menjalankan:
     ``` css
     python file_client_stress_test.py \
        --server-host 172.16.16.101 \
        --server-port 46666 \
        --server-workers {server_workers} \
        --output {description}_stress_test_results_<timestamp>.csv
     ```
   - `file_client_stress_test.py` melakukan:
     1. Enumerasi Kombinasi
        - operasi : upload, download
        - volume : 10, 50, 100 MB
        - client_workers : 1, 5, 50 <br>
          → Total 2×3×3 = 18 test per konfigurasi server.
     2. Untuk setiap kombinasi :
        - Jika operasi `download`, siapkan file “test_file_{volume}MB.txt” di lokal dan upload ke server dulu.
        - Buat `ThreadPoolExecutor` (client thread pool).
        - Submit `client_workers` banyak tugas `worker_task`:
          - upload :
            - buat file dummy `size` MB
            - kirim perintah `"UPLOAD <nama> \"<base64>\""` → server
          - download :
            - kirim perintah `"GET <nama>"` → server
          - list :
            - kirim perintah `"LIST"` → server
          - Masing-masing worker :
            - buka koneksi socket baru
            - kirim perintah, tunggu response hingga `\r\n\r\n`
            - decode JSON, simpan byte count, waktu, throughput, success/fail
        - Setelah semua selesai, hitung :
          - total_duration (dari client side)
          - rata-rata duration & throughput per worker
          - jumlah sukses/gagal client
        - Tambah metadata jumlah server workers & asumsi server sukses semua
        - Simpan ke list hasil
      3. Output CSV
         - Buat DataFrame lalu `to_csv("{description}_stress_test_results_<timestamp>.csv")`
         - Cetak ringkasan di console.
5. **Stop Server**
   - Setelah stress-test selesai, TestRunner memanggil `stop_server()` :
     - `terminate()` lalu `wait()` pada proses server
     - Jika perlu, `kill()`
   - Bersihkan state, lalu tunggu 2 detik.
6. **Iterasi Berikutnya** <br>
   Ulangi langkah Start Server → Run Stress Test → Stop Server untuk setiap konfigurasi.
7. **Akhir** <br>
   Setelah semua konfigurasi diuji, TestRunner mencetak ringkasan :
   ``` yaml
   Konfigurasi berhasil: X/6
   Konfigurasi yang gagal: Y/6
   ```
   Selesai
   
## 🌳 Alur Kerja / Arsitektur (Secara Singkat)
1. **Inisialisasi**  <br>
   `run_for_test.py` membuat `TestRunner` dan daftar konfigurasi server (1/5/50 workers × threading/multiprocessing).
2. **Iterasi Konfigurasi** : <br>
   Untuk tiap konfigurasi :
   1. Start Server (`file_thread_pool.py`) di port 46666 dengan pool worker sesuai (thread/process).
   2. Jalankan Stress Test (`file_client_stress_test.py`
      - Kombinasi operasi (upload/download), ukuran file (10/50/100 MB), dan client pool (1/5/50) → 18 test.
      - Setiap worker: buat koneksi TCP, kirim perintah (UPLOAD/GET/LIST), terima JSON, ukur durasi & throughput, catat sukses/gagal.
      - Hitung rata-rata metrik, simpan hasil ke CSV.
   3. Stop Server: hentikan proses server, bersihkan, tunggu sebentar.
3. **Akhir Pengujian** : Cetak ringkasan jumlah konfigurasi yang berhasil/gagal.

## 🌳 Diagram Arsitektur Alur Kerja
![Arsitektur Kerja](https://github.com/user-attachments/assets/8d32942d-038a-4868-913b-7cb23ccad587)

# 🌳 Penjelasan Tiap Class File
## ✨ file_interface.py
1. **Inisialisasi Direktori** <br>
   Pindah kerja ke folder files/ di mana semua operasi file berlangsung.
   ``` py
   class FileInterface:
    def __init__(self):
        os.chdir('files/')
   ```
2. **List File** <br>
   Mengembalikan daftar semua file dengan ekstensi di direktori.
   ``` py
   def list(self, params=[]):
    filelist = glob('*.*')
    return dict(status='OK', data=filelist)
   ```
3. **Delete File** <br>
   Menghapus filename jika ada, atau error jika tidak ditemukan.
   ``` py
   def delete(self, params=[]):
    filename = params[0]
    if os.path.exists(filename):
        os.remove(filename)
        return dict(status='OK', data=f'{filename} berhasil dihapus')
    return dict(status='ERROR', data='File not found')
   ```
4. **Upload File** <br>
   Decode Base64 dari klien, tulis ke file baru, atau laporkan jika sudah ada.
   ``` py
   def upload(self, params=[]):
    filename = params[0]
    if os.path.exists(filename):
        return dict(status='OK', data=f'{filename} file sudah ada')
    filedata = base64.b64decode(" ".join(params[1:]).encode())
    with open(filename, 'wb') as f:
        f.write(filedata)
    return dict(status='OK', data=f'File {filename} berhasil upload')
    ```
5. **Download File (GET)** <br>
   Baca file, encode ke Base64, dan kembalikan sebagai string.
   ``` py
   def get(self, params=[]):
    filename = params[0]
    with open(filename, 'rb') as fp:
        isifile = base64.b64encode(fp.read()).decode()
    return dict(status='OK', data_namafile=filename, data_file=isifile)
   ```
   
## ✨ file_thread_pool.py
File ini bertugas menjalankan server multi-threading menggunakan ThreadPoolExecutor agar server bisa menangani banyak koneksi klien sekaligus.
1. **Inisialisasi Konstanta dan Executor** <br>
   Membuat socket server di port 10000 dan executor dengan 10 thread untuk menangani permintaan klien secara paralel.
   ``` py
   almat_server = ('0.0.0.0', 10000)
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
   ```
2. **Fungsi recv_data** <br>
   Fungsi ini menangani satu koneksi :
   - Menerima request dari klien
   - Memprosesnya lewat proses_request()
   - Mengirim hasilnya kembali ke klien
   - Menutup koneksi
   ``` py
   def recv_data(conn):
    perintah = conn.recv(1024).decode()
    hasil = proses_request(perintah)
    hasil = json.dumps(hasil)
    conn.sendall(hasil.encode())
    conn.close()
   ```
3. **Fungsi proses_request** <br>
   Memproses request dengan :
   - FileProtocol : parsing request string (misal: upload namafile ...)
   - FileInterface: mengeksekusi perintah seperti upload, get, list, hapus
   - Mengembalikan hasil eksekusi sebagai dict
   ``` py
   def proses_request(request_str):
    fp = FileProtocol()
    fi = FileInterface()
    command, params = fp.proses_string(request_str)
    hasil = fi.proses(command, params)
    return hasil
   ```
4. **Main Loop Server** <br>
   Server :
   - Menerima koneksi dari klien
   - Menyerahkan penanganannya ke thread pool (`executor.submit`)
   - Proses `recv_data()` berjalan secara paralel untuk tiap klien
   ``` py
   if __name__ == '__main__':
    sock.bind(almat_server)
    sock.listen(100)
    while True:
        conn, client_addr = sock.accept()
        executor.submit(recv_data, conn)
   ```
## ✨ file_client_cli.py
File ini merupakan client CLI (Command Line Interface) untuk berkomunikasi dengan file server. Klien bisa mengirim perintah seperti upload, download, delete, dan list.
1. **Fungsi `send_command`** <br>
   Fungsi ini :
   - Membuat koneksi ke server
   - Mengirim perintah (string)
   - Menerima respons JSON dari server
   - Mengembalikan hasil sebagai dictionary
   ``` py
   def send_command(command_str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_ADDRESS, SERVER_PORT))
    sock.sendall(command_str.encode())
    data = sock.recv(1024)
    sock.close()
    return json.loads(data.decode())
   ```
2. **Fungsi `remote_list()`** <br>
   Mengirim perintah LIST ke server → mendapat daftar file yang tersedia.
   ``` py
   def remote_list():
    return send_command("LIST")
   ```
3. **Fungsi `remote_get(filename)`** <br>
   Mengirim GET filename ke server → menerima file (base64) → menyimpannya ke disk.
   ``` py
   def remote_get(filename):
    result = send_command(f"GET {filename}")
    if result['status'] == 'OK':
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(result['data']))
        return True
    return False
   ```
4. **Fungsi `remote_upload(filename)`** <br> 
   Membaca file lokal → encode base64 → kirim ke server dengan perintah UPLOAD.
   ``` py
   def remote_upload(filename):
    if not os.path.exists(filename):
        return False
    with open(filename, 'rb') as f:
        filedata = base64.b64encode(f.read()).decode()
    command_str = f"UPLOAD {filename} {filedata}"
    result = send_command(command_str)
    return result['status'] == 'OK'
   ```
5. **Fungsi `remote_delete(filename)`** <br>
   Mengirim perintah DELETE filename ke server untuk menghapus file di server.
   ``` py
   def remote_delete(filename):
    return send_command(f"DELETE {filename}")
   ```
## ✨ file_client_stress_test.py
File ini digunakan untuk melakukan stress test terhadap server file. Tujuannya adalah untuk **menguji ketahanan dan performa server** dengan melakukan upload dan download secara berulang dan bersamaan.
1. **Impor dan Konstanta** <br>
   - Mengimpor fungsi dari file_client_cli.py
   - Menentukan jumlah thread (klien paralel) dan jumlah iterasi per thread
   - Menentukan nama file yang akan di-upload/download
   ``` py
   import threading
   import time
   from file_client_cli import remote_upload, remote_get

   NUM_THREADS = 10
   NUM_ITERATIONS = 5
   FILENAME = "testfile.txt"
   ```
2. **Fungsi `upload_worker()`** <br>
   Setiap thread akan melakukan upload file sebanyak NUM_ITERATIONS kali.
   ``` py
   def upload_worker():
    for _ in range(NUM_ITERATIONS):
        remote_upload(FILENAME)
   ```
3. **Fungsi `download_worker()`** <br>
   Setiap thread akan mendownload file dari server NUM_ITERATIONS kali.
   ``` py
   def download_worker():
    for _ in range(NUM_ITERATIONS):
        remote_get(FILENAME)
   ```
4. **Fungsi `stress_test()`** <br>
   - Membuat dan memulai semua thread upload dan download
   - Menjalankan semua thread secara paralel
   - Menunggu semua thread selesai (join())
   ``` py
   def stress_test():
    upload_threads = [threading.Thread(target=upload_worker) for _ in range(NUM_THREADS)]
    download_threads = [threading.Thread(target=download_worker) for _ in range(NUM_THREADS)]

    for t in upload_threads + download_threads:
        t.start()
    for t in upload_threads + download_threads:
        t.join()
   ```
5. **Main Execution** <br>
   - Mengukur waktu eksekusi total
   - Menjalankan stress_test() saat file dijalankan langsung
   ``` py
   if __name__ == "__main__":
    start_time = time.time()
    stress_test()
    end_time = time.time()
    print(f"Stress test selesai dalam {end_time - start_time:.2f} detik")
   ```

## ✨ run_for_test.py
ile ini bertindak sebagai **entry point (titik awal eksekusi)** untuk menjalankan server dan menghubungkannya dengan klien untuk pengujian. File ini menyatukan berbagai komponen sistem dalam satu proses kontrol.
1. **Import Modul dan Fungsi** <br>
   Mengimpor :
   - start_server() dari file_thread_pool.py → Untuk memulai server
   - stress_test() dari file_client_stress_test.py → Untuk melakukan stress test (upload/download simultan)
   ``` py
   from file_thread_pool import start_server
   from file_client_stress_test import stress_test
   ```
2. **Fungsi main()** <br>
   Tahapan :
   - Membuat dan menjalankan server di thread terpisah (daemon=True agar otomatis mati saat program selesai)
   - Delay 2 detik untuk memastikan server siap sebelum klien mengakses
   - Memanggil stress_test() untuk memulai pengujian beban
   ``` py
   def main():
    import threading
    import time

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Tunggu beberapa detik untuk memastikan server aktif
    time.sleep(2)

    stress_test()
    ```
3. **Main Execution** <br>
   Menjalankan fungsi main() saat file ini dieksekusi langsung.
   ``` py
   if __name__ == "__main__":
    main()
   ```

## 🌳 Cara Pengerjaan
