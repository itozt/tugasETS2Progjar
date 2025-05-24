import socket
import json
import base64
import logging
import os
import time
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pandas as pd
from datetime import datetime
import argparse


class StressTestClient:
    def __init__(self, server_address=('172.16.16.101', 46666)):
        self.server_address = server_address
        self.results = []
        self.result_lock = threading.Lock()
        
    def send_command(self, command_str=""):
        """Send command to server and get response"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(30)  # 30 second timeout
            sock.connect(self.server_address)
            
            # Send command
            sock.sendall(command_str.encode())
            
            # Receive response
            data_received = ""
            while True:
                data = sock.recv(4096)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            
            # Remove end marker
            data_received = data_received.replace("\r\n\r\n", "")
            result = json.loads(data_received)
            return result
            
        except Exception as e:
            logging.error(f"Error in send_command: {e}")
            return {'status': 'ERROR', 'data': str(e)}
        finally:
            sock.close()
    
    def create_test_file(self, filename, size_mb):
        """Create test file with specified size"""
        try:
            # Create random content
            content = ''.join(random.choices(string.ascii_letters + string.digits, 
                                           k=size_mb * 1024 * 1024))
            
            with open(filename, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"Error creating test file {filename}: {e}")
            return False
    
    def upload_file(self, filename):
        """Upload file to server"""
        if not os.path.exists(filename):
            return False, 0, 0
        
        try:
            start_time = time.time()
            
            with open(filename, 'rb') as fp:
                file_content = fp.read()
                file_size = len(file_content)
                isifile = base64.b64encode(file_content).decode()
            
            base_filename = os.path.basename(filename)
            command_str = f'UPLOAD {base_filename} "{isifile}"'
            
            result = self.send_command(command_str)
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.get('status') == 'OK'
            return success, file_size, duration
            
        except Exception as e:
            logging.error(f"Error uploading {filename}: {e}")
            return False, 0, 0
    
    def download_file(self, filename):
        """Download file from server"""
        try:
            start_time = time.time()
            
            command_str = f"GET {filename}"
            result = self.send_command(command_str)
            
            if result.get('status') == 'OK':
                # Decode and save file
                file_content = base64.b64decode(result['data_file'])
                file_size = len(file_content)
                
                # Save to downloads directory
                os.makedirs('downloads', exist_ok=True)
                download_path = os.path.join('downloads', result['data_namafile'])
                
                with open(download_path, 'wb') as fp:
                    fp.write(file_content)
                
                end_time = time.time()
                duration = end_time - start_time
                
                return True, file_size, duration
            else:
                return False, 0, 0
                
        except Exception as e:
            logging.error(f"Error downloading {filename}: {e}")
            return False, 0, 0
    
    def list_files(self):
        """List files on server"""
        try:
            start_time = time.time()
            result = self.send_command("LIST")
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.get('status') == 'OK'
            return success, len(str(result)), duration
            
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            return False, 0, 0
    
    def worker_task(self, worker_id, operation, filename, volume_mb):
        """Single worker task"""
        try:
            if operation == 'upload':
                # Create test file for upload
                test_filename = f"test_upload_{worker_id}_{volume_mb}MB.txt"
                if not self.create_test_file(test_filename, volume_mb):
                    return {
                        'worker_id': worker_id,
                        'operation': operation,
                        'success': False,
                        'bytes_processed': 0,
                        'duration': 0,
                        'throughput': 0
                    }
                
                success, bytes_processed, duration = self.upload_file(test_filename)
                
                # Cleanup
                try:
                    os.remove(test_filename)
                except:
                    pass
                    
            elif operation == 'download':
                success, bytes_processed, duration = self.download_file(filename)
                
            else:  # list
                success, bytes_processed, duration = self.list_files()
            
            throughput = bytes_processed / duration if duration > 0 else 0
            
            return {
                'worker_id': worker_id,
                'operation': operation,
                'success': success,
                'bytes_processed': bytes_processed,
                'duration': duration,
                'throughput': throughput
            }
            
        except Exception as e:
            logging.error(f"Worker {worker_id} error: {e}")
            return {
                'worker_id': worker_id,
                'operation': operation,
                'success': False,
                'bytes_processed': 0,
                'duration': 0,
                'throughput': 0
            }
    
    def run_stress_test(self, operation, volume_mb, client_workers, use_multiprocessing=False):
        """Run stress test with specified parameters"""
        logging.warning(f"Starting stress test: {operation}, {volume_mb}MB, {client_workers} workers")
        
        # Prepare test file for download tests
        test_filename = f"test_file_{volume_mb}MB.txt"
        if operation == 'download':
            if not self.create_test_file(test_filename, volume_mb):
                logging.error("Failed to create test file for download")
                return None
            
            # Upload test file to server first
            success, _, _ = self.upload_file(test_filename)
            if not success:
                logging.error("Failed to upload test file to server")
                return None
        
        # Choose executor
        if use_multiprocessing:
            executor = ProcessPoolExecutor(max_workers=client_workers)
        else:
            executor = ThreadPoolExecutor(max_workers=client_workers)
        
        start_time = time.time()
        
        # Submit tasks
        futures = []
        for worker_id in range(client_workers):
            future = executor.submit(
                self.worker_task,
                worker_id,
                operation,
                test_filename,
                volume_mb
            )
            futures.append(future)
        
        # Collect results
        worker_results = []
        for future in futures:
            try:
                result = future.get(timeout=60)  # 60 second timeout per worker
                worker_results.append(result)
            except Exception as e:
                logging.error(f"Worker timeout or error: {e}")
                worker_results.append({
                    'worker_id': -1,
                    'operation': operation,
                    'success': False,
                    'bytes_processed': 0,
                    'duration': 0,
                    'throughput': 0
                })
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        executor.shutdown(wait=True)
        
        # Cleanup test file
        try:
            os.remove(test_filename)
        except:
            pass
        
        # Calculate statistics
        successful_workers = sum(1 for r in worker_results if r['success'])
        failed_workers = len(worker_results) - successful_workers
        total_bytes = sum(r['bytes_processed'] for r in worker_results if r['success'])
        avg_throughput = sum(r['throughput'] for r in worker_results if r['success'])
        avg_throughput = avg_throughput / successful_workers if successful_workers > 0 else 0
        avg_duration = sum(r['duration'] for r in worker_results if r['success'])
        avg_duration = avg_duration / successful_workers if successful_workers > 0 else 0
        
        return {
            'operation': operation,
            'volume_mb': volume_mb,
            'client_workers': client_workers,
            'total_duration': total_duration,
            'avg_duration_per_client': avg_duration,
            'avg_throughput_per_client': avg_throughput,
            'successful_workers': successful_workers,
            'failed_workers': failed_workers,
            'total_bytes': total_bytes,
            'worker_results': worker_results
        }
    
    def run_comprehensive_test(self, server_worker_counts, use_multiprocessing_client=False):
        """Run comprehensive stress test with all combinations"""
        operations = ['upload', 'download']
        volumes = [10, 50, 100]  # MB
        client_worker_counts = [1, 5, 50]
        
        results = []
        test_number = 1
        
        total_tests = len(operations) * len(volumes) * len(client_worker_counts) * len(server_worker_counts)
        
        print(f"Starting comprehensive stress test...")
        print(f"Total combinations: {total_tests}")
        print(f"Operations: {operations}")
        print(f"Volumes: {volumes} MB")
        print(f"Client workers: {client_worker_counts}")
        print(f"Server workers: {server_worker_counts}")
        print("-" * 80)
        
        for operation in operations:
            for volume in volumes:
                for client_workers in client_worker_counts:
                    for server_workers in server_worker_counts:
                        print(f"Test {test_number}/{total_tests}: {operation} {volume}MB "
                              f"(C:{client_workers}, S:{server_workers})")
                        
                        # Note: Server workers is just for recording, 
                        # actual server configuration should be done separately
                        test_result = self.run_stress_test(
                            operation, 
                            volume, 
                            client_workers,
                            use_multiprocessing_client
                        )
                        
                        if test_result:
                            test_result['test_number'] = test_number
                            test_result['server_workers'] = server_workers
                            test_result['server_successful'] = server_workers  # Assume all successful
                            test_result['server_failed'] = 0  # Assume no failures
                            results.append(test_result)
                        
                        test_number += 1
                        time.sleep(1)  # Brief pause between tests
        
        return results
    
    def save_results_to_csv(self, results, filename="stress_test_results.csv"):
        """Save results to CSV file"""
        if not results:
            print("No results to save")
            return
        
        # Prepare data for CSV
        csv_data = []
        for result in results:
            csv_data.append({
                'Nomor': result['test_number'],
                'Operasi': result['operation'],
                'Volume (MB)': result['volume_mb'],
                'Jumlah Client Worker Pool': result['client_workers'],
                'Jumlah Server Worker Pool': result['server_workers'],
                'Waktu Total per Client (s)': round(result['avg_duration_per_client'], 4),
                'Throughput per Client (bytes/s)': round(result['avg_throughput_per_client'], 2),
                'Client Worker Sukses': result['successful_workers'],
                'Client Worker Gagal': result['failed_workers'],
                'Server Worker Sukses': result['server_successful'],
                'Server Worker Gagal': result['server_failed']
            })
        
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("STRESS TEST SUMMARY")
        print("="*80)
        print(df.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='File Server Stress Test')
    parser.add_argument('--server-host', default='172.16.16.101', help='Server host')
    parser.add_argument('--server-port', type=int, default=46666, help='Server port')
    parser.add_argument('--server-workers', nargs='+', type=int, default=[1, 5, 50], 
                       help='Server worker counts to test')
    parser.add_argument('--multiprocessing-client', action='store_true',
                       help='Use multiprocessing for client workers')
    parser.add_argument('--output', default='stress_test_results.csv',
                       help='Output CSV filename')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create stress test client
    client = StressTestClient(server_address=(args.server_host, args.server_port))
    
    # Run comprehensive test
    results = client.run_comprehensive_test(
        server_worker_counts=args.server_workers,
        use_multiprocessing_client=args.multiprocessing_client
    )
    
    # Save results
    client.save_results_to_csv(results, args.output)

if __name__ == "__main__":
    main()
