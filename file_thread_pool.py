from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp


from file_protocol import FileProtocol

class ThreadPoolServer:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=5, use_multiprocessing=False):
        self.ipinfo = (ipaddress, port)
        self.max_workers = max_workers
        self.use_multiprocessing = use_multiprocessing
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.active_workers = 0
        self.successful_workers = 0
        self.failed_workers = 0
        self.worker_lock = threading.Lock()
        
        # Create executor based on type
        if use_multiprocessing:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_client_connection(self, connection, client_address):
        """Process client connection in worker thread/process"""
        fp = FileProtocol()
        
        with self.worker_lock:
            self.active_workers += 1
        
        try:
            logging.warning(f"Processing connection from {client_address}")
            
            while True:
                data = connection.recv(1024)  # Increased buffer size
                if data:
                    data_str = data.decode()
                    hasil = fp.proses_string(data_str)
                    # Add end marker as per protocol
                    response = hasil + "\r\n\r\n"
                    connection.sendall(response.encode())
                else:
                    break
            
            with self.worker_lock:
                self.successful_workers += 1
                
        except Exception as e:
            logging.error(f"Error processing client {client_address}: {e}")
            with self.worker_lock:
                self.failed_workers += 1
        finally:
            connection.close()
            with self.worker_lock:
                self.active_workers -= 1

    def run(self):
        """Run the server"""
        logging.warning(f"Thread pool server running at {self.ipinfo} with {self.max_workers} workers")
        logging.warning(f"Using {'multiprocessing' if self.use_multiprocessing else 'multithreading'}")
        
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(10)
        
        try:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"Connection from {client_address}")
                
                # Submit task to executor
                future = self.executor.submit(
                    self.process_client_connection, 
                    connection, 
                    client_address
                )
                
        except KeyboardInterrupt:
            logging.warning("Server shutting down...")
        finally:
            self.executor.shutdown(wait=True)
            self.my_socket.close()
    
    def get_worker_stats(self):
        """Get worker statistics"""
        with self.worker_lock:
            return {
                'active': self.active_workers,
                'successful': self.successful_workers,
                'failed': self.failed_workers,
                'total_processed': self.successful_workers + self.failed_workers
            }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='File Server with Thread/Process Pool')
    parser.add_argument('--port', type=int, default=46666, help='Server port')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads/processes')
    parser.add_argument('--multiprocessing', action='store_true', help='Use multiprocessing instead of threading')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    server = ThreadPoolServer(
        ipaddress='0.0.0.0',
        port=args.port,
        max_workers=args.workers,
        use_multiprocessing=args.multiprocessing
    )
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        stats = server.get_worker_stats()
        print(f"Final stats: {stats}")

if __name__ == "__main__":
    main()
