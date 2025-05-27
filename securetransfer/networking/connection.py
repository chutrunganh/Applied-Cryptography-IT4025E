"""
SecureTransfer - Network Manager
Handles network connections for P2P file transfers
"""

import os
import json
import socket
import threading
import time
import uuid
import requests

# Optional ngrok support
try:
    from pyngrok import ngrok, conf
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False


class ConnectionType:
    LOCAL = "local"
    DIRECT = "direct"
    NGROK = "ngrok"
    RELAY = "relay"


class TransferStatus:
    WAITING = "waiting"
    CONNECTING = "connecting"
    TRANSFERRING = "transferring"
    COMPLETE = "complete"
    FAILED = "failed"


class NetworkManager:
    """Enhanced network management for secure P2P transfers"""
    
    def __init__(self, default_port=5000):
        """Initialize with configuration options"""
        self.default_port = default_port
        self.active_transfers = {}
        self.status_callback = None
        
        # Auto-detect local IP
        self.local_ip = self._get_local_ip()
          # Initialize ngrok if available
        self.ngrok_tunnel = None
        
        # Load ngrok authtoken from settings if available
        try:
            from ..data.database import DatabaseManager
            db_manager = DatabaseManager()
            settings = db_manager.get_settings()
            if NGROK_AVAILABLE and "ngrok_authtoken" in settings:
                conf.get_default().auth_token = settings["ngrok_authtoken"]
        except Exception:
            # Non-critical error, can still work without ngrok
            pass
        
    def set_status_callback(self, callback):
        """Set a callback function for status updates: callback(transfer_id, status, message)"""
        self.status_callback = callback
    
    def _update_status(self, transfer_id, status, message=None):
        """Update transfer status and call the callback if set"""
        if transfer_id not in self.active_transfers:
            self.active_transfers[transfer_id] = {}
            
        self.active_transfers[transfer_id]["status"] = status
        self.active_transfers[transfer_id]["message"] = message
        self.active_transfers[transfer_id]["updated_at"] = time.time()
        
        # Call the callback if set
        if self.status_callback:
            self.status_callback(transfer_id, status, message)
    
    def _get_local_ip(self):
        """Get the local IP address of this machine"""
        try:
            # This doesn't actually send data, just creates a socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def _get_public_ip(self):
        """Get the public IP address of this machine"""
        try:
            response = requests.get('https://api.ipify.org').text
            return response
        except:
            return None
    
    def start_server(self, transfer_id, port=None, connection_type=ConnectionType.LOCAL):
        """
        Start a server to send a file
        Returns server info dictionary
        """
        if not port:
            port = self.default_port
            
        # Update status
        self._update_status(transfer_id, TransferStatus.WAITING, "Starting server")
        
        # Create a unique server ID
        server_id = str(uuid.uuid4())
        
        # Set up socket
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind to the port
            listener.bind(("0.0.0.0", port))
            listener.listen(1)
            
            # Store server info
            server_info = {
                "server_id": server_id,
                "transfer_id": transfer_id,
                "socket": listener,
                "port": port,
                "local_address": f"{self.local_ip}:{port}",
                "public_address": None
            }
            
            # Handle different connection types
            if connection_type == ConnectionType.NGROK:
                if not NGROK_AVAILABLE:
                    raise Exception("Ngrok is not available. Please install pyngrok package.")
                    
                # Start ngrok tunnel
                self.ngrok_tunnel = ngrok.connect(port, "tcp")
                server_info["public_address"] = self.ngrok_tunnel.public_url
                
            elif connection_type == ConnectionType.DIRECT:
                public_ip = self._get_public_ip()
                if public_ip:
                    server_info["public_address"] = f"{public_ip}:{port}"
            
            # Store in active transfers
            self.active_transfers[transfer_id]["server"] = server_info
            
            # Update status
            self._update_status(transfer_id, TransferStatus.WAITING, 
                             f"Server started on port {port}")
            
            return server_info
            
        except Exception as e:
            self._update_status(transfer_id, TransferStatus.FAILED, f"Failed to start server: {e}")
            raise
    
    def stop_server(self, transfer_id):
        """Stop the server for a transfer"""
        if transfer_id in self.active_transfers and "server" in self.active_transfers[transfer_id]:
            server_info = self.active_transfers[transfer_id]["server"]
            
            # Close the socket
            if "socket" in server_info:
                try:
                    server_info["socket"].close()
                except:
                    pass
            
            # Close ngrok tunnel if it was used
            if self.ngrok_tunnel:
                try:
                    ngrok.disconnect(self.ngrok_tunnel.public_url)
                    self.ngrok_tunnel = None
                except:
                    pass
            
            # Update status
            self._update_status(transfer_id, TransferStatus.COMPLETE, "Server stopped")
    
    def accept_connection(self, transfer_id):
        """
        Wait for a client to connect to our server
        Returns the connected socket or None if failed
        """
        if transfer_id not in self.active_transfers or "server" not in self.active_transfers[transfer_id]:
            raise ValueError(f"No server found for transfer {transfer_id}")
            
        server_info = self.active_transfers[transfer_id]["server"]
        listener = server_info["socket"]
        
        try:
            # Set a timeout for the accept call
            listener.settimeout(300)  # 5 minutes timeout
            
            # Update status
            self._update_status(transfer_id, TransferStatus.WAITING, 
                             "Waiting for connection")
            
            # Accept connection
            conn, addr = listener.accept()
            
            # Update status
            self._update_status(transfer_id, TransferStatus.CONNECTING, 
                             f"Connection from {addr[0]}:{addr[1]}")
            
            return conn
            
        except socket.timeout:
            self._update_status(transfer_id, TransferStatus.FAILED, 
                             "Connection timeout")
            return None
        except Exception as e:
            self._update_status(transfer_id, TransferStatus.FAILED, 
                             f"Connection failed: {e}")
            return None
    
    def connect_to_server(self, transfer_id, host, port):
        """
        Connect to a server
        Returns the connected socket or None if failed
        """
        try:
            # Update status
            self._update_status(transfer_id, TransferStatus.CONNECTING, 
                             f"Connecting to {host}:{port}")
            
            # Create socket and connect
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((host, port))
            
            # Update status
            self._update_status(transfer_id, TransferStatus.CONNECTING, 
                             f"Connected to {host}:{port}")
            
            # Store in active transfers
            if transfer_id not in self.active_transfers:
                self.active_transfers[transfer_id] = {}
                
            self.active_transfers[transfer_id]["connection"] = conn
            
            return conn
            
        except Exception as e:
            self._update_status(transfer_id, TransferStatus.FAILED, 
                             f"Connection failed: {e}")
            return None
    
    def send_file(self, conn, transfer_id, filepath):
        """
        Send a file over a connected socket
        """
        try:
            # Get file info
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            # Update status
            self._update_status(transfer_id, TransferStatus.TRANSFERRING, 
                             f"Sending {filename} ({filesize} bytes)")
            
            # Send header with file info
            header = json.dumps({
                "filename": filename,
                "filesize": filesize,
                "transfer_id": transfer_id
            }).encode() + b"\n"
            conn.sendall(header)
            
            # Send the file in chunks
            sent_bytes = 0
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)  # 64KB chunks
                    if not chunk:
                        break
                        
                    conn.sendall(chunk)
                    sent_bytes += len(chunk)
                      # Update status periodically (every ~1MB)
                    if sent_bytes % (1024 * 1024) < (64 * 1024):
                        progress = min(100, int(sent_bytes * 100 / filesize))
                        self._update_status(transfer_id, TransferStatus.TRANSFERRING, 
                                         f"Sending: {progress}% complete")
            
            # Update status
            self._update_status(transfer_id, TransferStatus.COMPLETE, 
                             f"File sent successfully")
            
            # Auto-cleanup after successful transfer
            self._auto_cleanup_after_transfer(transfer_id, True)
            
        except Exception as e:
            self._update_status(transfer_id, TransferStatus.FAILED, 
                             f"Send failed: {e}")
            # Auto-cleanup after failed transfer
            self._auto_cleanup_after_transfer(transfer_id, False)
            raise
    
    def receive_file(self, conn, transfer_id, output_dir):
        """
        Receive a file over a connected socket
        Returns the path to the received file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Receive header
            header_buffer = b""
            while b"\n" not in header_buffer:
                chunk = conn.recv(1024)
                if not chunk:
                    raise ConnectionError("Connection closed before receiving header")
                header_buffer += chunk
                
            # Parse header
            header_line, rest = header_buffer.split(b"\n", 1)
            info = json.loads(header_line.decode())
            
            filename = info["filename"]
            filesize = info["filesize"]
            
            # Update status
            self._update_status(transfer_id, TransferStatus.TRANSFERRING, 
                             f"Receiving {filename} ({filesize} bytes)")
            
            # Create output file
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                # Write the extra data we already received
                if rest:
                    f.write(rest)
                    received = len(rest)
                else:
                    received = 0
                
                # Receive the rest of the file
                while received < filesize:
                    chunk = conn.recv(64 * 1024)  # 64KB chunks
                    if not chunk:
                        raise ConnectionError("Connection closed prematurely")
                        
                    f.write(chunk)
                    received += len(chunk)
                    
                    # Update status periodically (every ~1MB)
                    if received % (1024 * 1024) < (64 * 1024):
                        progress = min(100, int(received * 100 / filesize))
                        self._update_status(transfer_id, TransferStatus.TRANSFERRING, 
                                         f"Receiving: {progress}% complete")
              # Update status
            self._update_status(transfer_id, TransferStatus.COMPLETE, 
                             f"File received successfully")
            
            # Auto-cleanup after successful transfer
            self._auto_cleanup_after_transfer(transfer_id, True)
            
            return output_path
            
        except Exception as e:
            self._update_status(transfer_id, TransferStatus.FAILED, 
                             f"Receive failed: {e}")
            # Auto-cleanup after failed transfer
            self._auto_cleanup_after_transfer(transfer_id, False)
            raise
    
    def _auto_cleanup_after_transfer(self, transfer_id, success):
        """Automatically clean up after a transfer completes"""
        try:
            from ..data.database import DatabaseManager
            db_manager = DatabaseManager()
            db_manager.auto_cleanup_on_transfer_complete(transfer_id, success)
        except Exception as e:
            print(f"Error during auto-cleanup for transfer {transfer_id}: {e}")
    
    def cleanup_all_transfers(self):
        """Clean up all active transfers and temporary files"""
        try:
            from ..data.database import DatabaseManager
            db_manager = DatabaseManager()
            db_manager.cleanup_temp_files()
            
            # Close any open ngrok tunnels
            if self.ngrok_tunnel:
                try:
                    from pyngrok import ngrok
                    ngrok.disconnect(self.ngrok_tunnel.public_url)
                    self.ngrok_tunnel = None
                except:
                    pass
            
            print("All transfers cleaned up")
        except Exception as e:
            print(f"Error during cleanup: {e}")
