# Tugas ETS Pemrograman Jaringan
## Daftar Isi
- [Soal](https://github.com/itozt/tugasETSProgjar/tree/main#-soal)
- [Kegunaan Masing-Masing File](https://github.com/itozt/tugasETSProgjar/tree/main#-kegunaan-masing-masing-file)
- [Alur Kerja / Arsitektur](https://github.com/itozt/tugasETSProgjar/tree/main#-alur-kerja--arsitektur)
- [Alur Kerja / Arsitektur (Secara Singkat)](https://github.com/itozt/tugasETSProgjar/tree/main#-alur-kerja--arsitektur-secara-singkat)
- [Diagram Arsitektur Alur Kerja](https://github.com/itozt/tugasETSProgjar/tree/main#-diagram-arsitektur-alur-kerja)
- Penjelasan Tiap Class File
  - [file_interface.py]()
  - [file_thread_pool.py]()
  - [file_client_cli.py]()
  - [file_client_stress_test.py]()
  - [run_for_test.py]()

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
2. **List File**
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
4. **Upload File**
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
5. **Download File (GET)**
   Baca file, encode ke Base64, dan kembalikan sebagai string.
   ``` py
   def get(self, params=[]):
    filename = params[0]
    with open(filename, 'rb') as fp:
        isifile = base64.b64encode(fp.read()).decode()
    return dict(status='OK', data_namafile=filename, data_file=isifile)
   ```
