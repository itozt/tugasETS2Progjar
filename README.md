# Tugas ETS Pemrograman Jaringan
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
1. **Inisialisasi**  `run_for_test.py` membuat `TestRunner` dan daftar konfigurasi server (1/5/50 workers × threading/multiprocessing).
2. **Iterasi Konfigurasi** : Untuk tiap konfigurasi :
   1. Start Server (`file_thread_pool.py`) di port 46666 dengan pool worker sesuai (thread/process).
   2. Jalankan Stress Test (`file_client_stress_test.py`
      - Kombinasi operasi (upload/download), ukuran file (10/50/100 MB), dan client pool (1/5/50) → 18 test.
      - Setiap worker: buat koneksi TCP, kirim perintah (UPLOAD/GET/LIST), terima JSON, ukur durasi & throughput, catat sukses/gagal.
      - Hitung rata-rata metrik, simpan hasil ke CSV.
   3. Stop Server: hentikan proses server, bersihkan, tunggu sebentar.
3. Akhir Pengujian: Cetak ringkasan jumlah konfigurasi yang berhasil/gagal.
