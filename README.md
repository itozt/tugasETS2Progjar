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

## 🌳 Cara Pengerjaan
