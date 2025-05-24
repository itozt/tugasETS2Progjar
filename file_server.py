from socket import *
import socket
import threading
import logging
import time
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

from file_protocol import FileProtocol

class LegacyServer(threading.Thread):
    """Original threading implementation for comparison"""
    def __init__(self, ipaddress='0.0.0.0', port=8889):
        self.ipinfo = (ipaddress, port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"Legacy server running at {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"Connection from {client_address}")

            clt = ProcessTheClient(connection, client_address)
            clt.start()
            self.the_clients.append(clt)

class ProcessTheClient(threading.Thread):
    """Legacy client processing thread"""
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        fp = FileProtocol()
        while True:
            data = self.connection.recv(1024)
            if data:
                data_str = data.decode()
                hasil = fp.proses_string(data_str)
                
                response = hasil + "\r\n\r\n"
                self.connection.sendall(response.encode())
            else:
                break
        self.connection.close()

class PoolServer:
    """Enhanced server with thread/process pool support"""
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=5, use_multiprocessing=False):
        self.ipinfo = (ipaddress, port)
        self.max_workers = max_workers
        self.use_multiprocessing = use_multiprocessing
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Statistics tracking
        self.active_workers = 0
        self.successful_workers = 0
        self.failed_workers = 0
        self.total_requests = 0
        self.worker_lock = threading.Lock()
        
        # Create executor based on type
        if use_multiprocessing:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
            self.server_type = "multiprocessing"
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            self.server_type = "multithreading"
    
    def process_client_connection(self, connection, client_address):
        """Process client connection in worker thread/process"""
        fp = FileProtocol()
        
        with self.worker_lock:
            self.active_workers += 1
            self.total_requests += 1
            current_request = self.total_requests
        
        try:
            logging.warning(f"Worker processing connection from {client_address} (Request #{current_request})")
            
            while True:
                data = connection.recv(1024)
                if data:
                    data_str = data.decode()
                    if data_str.strip():  # Only process non-empty commands
                        hasil = fp.proses_string(data_str)
                        # Add protocol end marker
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
            try:
                connection.close()
            except:
                pass
            with self.worker_lock:
                self.active_workers -= 1

    def run(self):
        """Run the server"""
        logging.warning(f"Pool server running at {self.ipinfo}")
        logging.warning(f"Mode: {self.server_type} with {self.max_workers} workers")
        
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(10)  # Increased backlog
        
        try:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"New connection from {client_address}")
                
                # Submit task to executor
                future = self.executor.submit(
                    self.process_client_connection, 
                    connection, 
                    client_address
                )
                
        except KeyboardInterrupt:
            logging.warning("Server shutting down...")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the server"""
        logging.warning("Shutting down server...")
        
        # Close socket
        try:
            self.my_socket.close()
        except:
            pass
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Print final statistics
        stats = self.get_worker_stats()
        logging.warning(f"Final server statistics: {stats}")
    
    def get_worker_stats(self):
        """Get worker statistics"""
        with self.worker_lock:
            return {
                'server_type': self.server_type,
                'max_workers': self.max_workers,
                'active_workers': self.active_workers,
                'successful_workers': self.successful_workers,
                'failed_workers': self.failed_workers,
                'total_requests': self.total_requests
            }

def main():
    parser = argparse.ArgumentParser(description='Enhanced File Server')
    parser.add_argument('--port', type=int, default=8889, help='Server port')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads/processes')
    parser.add_argument('--multiprocessing', action='store_true', 
                       help='Use multiprocessing instead of threading')
    parser.add_argument('--legacy', action='store_true', 
                       help='Use legacy threading implementation')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'server_{args.port}.log')
        ]
    )
    
    try:
        if args.legacy:
            print(f"Starting legacy server on {args.host}:{args.port}")
            server = LegacyServer(ipaddress=args.host, port=args.port)
            server.start()
            server.join()
        else:
            print(f"Starting {'multiprocessing' if args.multiprocessing else 'multithreading'} "
                  f"pool server on {args.host}:{args.port} with {args.workers} workers")
            
            server = PoolServer(
                ipaddress=args.host,
                port=args.port,
                max_workers=args.workers,
                use_multiprocessing=args.multiprocessing
            )
            server.run()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        if not args.legacy:
            stats = server.get_worker_stats()
            print(f"Final statistics: {stats}")
    except Exception as e:
        print(f"Server error: {e}")
        logging.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
