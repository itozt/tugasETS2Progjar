"""
Skrip untuk menjalankan pengujian server file yang komprehensif
Skrip ini akan membantu Anda menjalankan berbagai konfigurasi server dan uji stres
"""

import subprocess
import time
import os
import signal
import sys
import argparse
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.server_process = None
        
    def start_server(self, port=46666, workers=5, use_multiprocessing=False):
        """Start the server with specified configuration"""
        cmd = [
            sys.executable, 'thread_pool.py',
            '--port', str(port),
            '--workers', str(workers)
        ]
        
        if use_multiprocessing:
            cmd.append('--multiprocessing')
        
        print(f"Starting server: {' '.join(cmd)}")
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Berikan waktu pada server untuk memulai
            
            if self.server_process.poll() is None:
                print(f"Server berhasil dimulai (PID: {self.server_process.pid})")
                return True
            else:
                print("Server gagal memulai")
                return False
                
        except Exception as e:
            print(f"Error saat memulai server: {e}")
            return False
    
    def stop_server(self):
        """Stop server yang sedang berjalan"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("Server berhasil dihentikan")
            except subprocess.TimeoutExpired:
                print("Server tidak berhenti dengan baik, killing...")
                self.server_process.kill()
                self.server_process.wait()
            except Exception as e:
                print(f"Error menghentikan server: {e}")
        
        self.server_process = None
    
    def run_stress_test(self, server_workers, client_multiprocessing=False, output_prefix=""):
        """Jalankan uji stres dengan konfigurasi yang ditentukan"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_prefix}stress_test_results_{timestamp}.csv"
        
        cmd = [
            sys.executable, 'file_client_stress_test.py',
            '--server-host', '172.16.16.101',
            '--server-port', '46666',
            '--server-workers'
        ] + [str(w) for w in server_workers] + [
            '--output', output_file
        ]
        
        if client_multiprocessing:
            cmd.append('--multiprocessing-client')
        
        print(f"Running stress test: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # timeout dalam 1 jam
            
            if result.returncode == 0:
                print("Stress test berhasil diselesaikan")
                print(f"Hasil disimpan ke: {output_file}")
                return True
            else:
                print("Stress test gagal")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("Stress test timed out")
            return False
        except Exception as e:
            print(f"Error menjalankan stress test: {e}")
            return False
    
    def run_comprehensive_tests(self):
        """Jalankan pengujian komprehensif dengan konfigurasi server yang berbeda"""
        test_configs = [
            # (server_workers, emnggunakan_multiprocessing_atautidak, deskripsi)
            (1, False, "1worker_threading"),
            (5, False, "5workers_threading"),
            (50, False, "50workers_threading"),
            (1, True, "1worker_multiprocessing"),
            (5, True, "5workers_multiprocessing"),
            (50, True, "50workers_multiprocessing"),
        ]
        
        print("="*80)
        print("UJI STRES SERVER FILE KOMPREHENSIF")
        print("="*80)
        print(f"Total konfigurasi untuk diuji: {len(test_configs)}")
        print("Setiap konfigurasi akan diuji:")
        print("- Operasi: upload, download")
        print("- File size: 10MB, 50MB, 100MB")
        print("- Client worker: 1, 5, 50")
        print("- Total kombinasi per config: 18")
        print(f"- Grand total tests: {len(test_configs) * 18}")
        print("="*80)
        
        successful_configs = 0
        
        for i, (workers, use_mp, description) in enumerate(test_configs, 1):
            print(f"\n[{i}/{len(test_configs)}] Konfigurasi pengujian: {description}")
            print(f"Server workers: {workers}, Multiprocessing: {use_mp}")
            print("-" * 60)
            
            # Mulai server dengan konfigurasi saat ini
            if self.start_server(workers=workers, use_multiprocessing=use_mp):
                # Run stress test
                server_workers_list = [workers]  # Uji dengan jumlah pekerja server saat ini
                
                if self.run_stress_test(
                    server_workers=server_workers_list,
                    client_multiprocessing=False,  # Uji dengan klien threading
                    output_prefix=f"{description}_"
                ):
                    successful_configs += 1
                    print(f"✓ Configuration {description} completed successfully")
                else:
                    print(f"✗ Configuration {description} failed")
                
                # Stop server
                self.stop_server()
                time.sleep(2)  # Jeda singkat antara konfigurasi
            else:
                print(f"✗ Gagal memulai server untuk konfigurasi {description}")
        
        print("\n" + "="*80)
        print("RINGKASAN UJI KOMPREHENSIF")
        print("="*80)
        print(f"Konfigurasi berhasil: {successful_configs}/{len(test_configs)}")
        print(f"Konfigurasi yang gagal: {len(test_configs) - successful_configs}/{len(test_configs)}")
        
        if successful_configs == len(test_configs):
            print("✨ Semua pengujian berhasil diselesaikan! ✨")
        else:
            print("‼️ Beberapa pengujian gagal. Periksa log di atas untuk detailnya.")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_server()

def main():
    parser = argparse.ArgumentParser(description='File Server Test Runner')
    parser.add_argument('--mode', choices=['single', 'comprehensive'], default='comprehensive',
                       help='Test mode: single configuration or comprehensive test')
    parser.add_argument('--server-workers', type=int, default=5,
                       help='Number of server workers (single mode only)')
    parser.add_argument('--server-multiprocessing', action='store_true',
                       help='Use multiprocessing for server (single mode only)')
    parser.add_argument('--client-multiprocessing', action='store_true',
                       help='Use multiprocessing for client workers (single mode only)')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        if args.mode == 'single':
            print("Menjalankan single configuration test...")
            print(f"Server: {args.server_workers} workers, "
                  f"{'multiprocessing' if args.server_multiprocessing else 'threading'}")
            print(f"Client: {'multiprocessing' if args.client_multiprocessing else 'threading'}")
            
            if runner.start_server(
                workers=args.server_workers,
                use_multiprocessing=args.server_multiprocessing
            ):
                runner.run_stress_test(
                    server_workers=[args.server_workers],
                    client_multiprocessing=args.client_multiprocessing,
                    output_prefix="single_test_"
                )
            else:
                print("Gagal memulai server")
                
        else:  
            runner.run_comprehensive_tests()
            
    except KeyboardInterrupt:
        print("\nTes diinterupsi oleh user")
    finally:
        runner.cleanup()

if __name__ == "__main__":
    main()
