"""
SecureTransfer - Database Module
Handles persistent storage of transfer history and application settings
"""

import os
import json
import sqlite3
import time
from datetime import datetime


class DatabaseManager:
    """
    Database Manager for the SecureTransfer application
    Handles both JSON-based configuration and SQLite for transfer history
    """
    
    def __init__(self):
        """Initialize the database connections"""
        # Ensure data directory exists
        self.data_dir = os.path.join("securetransfer", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up the SQLite database for transfer history
        self.db_path = os.path.join(self.data_dir, "transfer_history.db")
        self._initialize_database()
        
        # Settings file path
        self.settings_path = os.path.join(self.data_dir, "settings.json")
        self._initialize_settings()
    
    def _initialize_database(self):
        """Initialize the SQLite database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create transfers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filepath TEXT,
            filesize INTEGER,
            sender TEXT,
            recipient TEXT,
            timestamp INTEGER,
            direction TEXT,
            status TEXT,
            connection_type TEXT,
            checksum TEXT,
            duration REAL,
            success INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_settings(self):
        """Initialize the settings file if it doesn't exist"""
        if not os.path.exists(self.settings_path):
            default_settings = {
                "download_directory": os.path.join("securetransfer", "data", "downloads"),
                "default_port": 5000,
                "default_connection_type": "local",
                "encryption_strength": "HIGH",
                "signature_algorithm": "SHA256",
                "theme": "dark",
                "auto_accept_transfers": False,
                "notify_on_complete": True,
                "max_concurrent_transfers": 3,
                "chunk_size": 2097152  # 2MB in bytes
            }
            
            with open(self.settings_path, "w") as f:
                json.dump(default_settings, f, indent=2)
    
    def get_settings(self):
        """Load settings from the JSON file"""
        if not os.path.exists(self.settings_path):
            self._initialize_settings()
            
        with open(self.settings_path, "r") as f:
            return json.load(f)
    
    def update_setting(self, key, value):
        """Update a single setting"""
        settings = self.get_settings()
        settings[key] = value
        
        with open(self.settings_path, "w") as f:
            json.dump(settings, f, indent=2)
    
    def update_settings(self, new_settings):
        """Update multiple settings at once"""
        settings = self.get_settings()
        settings.update(new_settings)
        
        with open(self.settings_path, "w") as f:
            json.dump(settings, f, indent=2)
    
    def add_transfer_record(self, transfer_info):
        """Add a new transfer record to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO transfers (
            id, filename, filepath, filesize, sender, recipient,
            timestamp, direction, status, connection_type, checksum, duration, success
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transfer_info.get('id'),
            transfer_info.get('filename'),
            transfer_info.get('filepath'),
            transfer_info.get('filesize'),
            transfer_info.get('sender'),
            transfer_info.get('recipient'),
            transfer_info.get('timestamp', int(time.time())),
            transfer_info.get('direction'),  # 'send' or 'receive'
            transfer_info.get('status'),
            transfer_info.get('connection_type'),            
            transfer_info.get('checksum'),
            transfer_info.get('duration'),
            1 if transfer_info.get('success', False) else 0
        ))
        
        conn.commit()
        conn.close()
    
    def update_transfer_status(self, transfer_id, status, success=None):
        """Update the status of an existing transfer record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if success is not None:
            cursor.execute(
                'UPDATE transfers SET status = ?, success = ? WHERE id = ?', 
                (status, 1 if success else 0, transfer_id)
            )
        else:
            cursor.execute(
                'UPDATE transfers SET status = ? WHERE id = ?', 
                (status, transfer_id)
            )
        
        conn.commit()
        conn.close()
    
    def get_transfer_history(self, limit=50):
        """Get the most recent transfer history records"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM transfers 
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Format timestamps for display
        for record in records:
            if record['timestamp']:
                dt = datetime.fromtimestamp(record['timestamp'])
                record['formatted_time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return records
    
    def get_transfer_details(self, transfer_id):
        """Get detailed information about a specific transfer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM transfers WHERE id = ?', (transfer_id,))
        record = cursor.fetchone()
        conn.close()
        
        if record:
            result = dict(record)
            # Format timestamp for display
            if result['timestamp']:
                dt = datetime.fromtimestamp(result['timestamp'])
                result['formatted_time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
            return result
        
        return None
    
    def search_transfers(self, query):
        """Search transfers by filename, sender, recipient, or status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build a query with LIKE clauses for various fields
        search_term = f"%{query}%"
        cursor.execute('''
        SELECT * FROM transfers 
        WHERE filename LIKE ? OR sender LIKE ? OR recipient LIKE ? OR status LIKE ?
        ORDER BY timestamp DESC
        ''', (search_term, search_term, search_term, search_term))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Format timestamps for display
        for record in records:
            if record['timestamp']:
                dt = datetime.fromtimestamp(record['timestamp'])
                record['formatted_time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return records
    
    def cleanup_temp_files(self):
        """Automatically clean up temporary files after transfer completion"""
        temp_dir = os.path.join(self.data_dir, "temp")
        if os.path.exists(temp_dir):
            import shutil
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:                    
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        print(f"Cleaned temp file: {item}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"Cleaned temp directory: {item}")
                except Exception as e:
                    print(f"Error cleaning temp item {item}: {e}")
    
    def cleanup_completed_transfer(self, transfer_id):
        """Clean up transfer folder after successful completion"""
        transfer_dir = os.path.join(self.data_dir, "transfers", transfer_id)
        if os.path.exists(transfer_dir):
            import shutil
            try:
                shutil.rmtree(transfer_dir)
                print(f"Cleaned up transfer directory: {transfer_id}")
            except Exception as e:
                print(f"Error cleaning transfer directory {transfer_id}: {e}")
    
    def cleanup_old_transfers(self, days_old=7):
        """Clean up old transfer folders and records older than specified days"""
        import shutil
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        print(f"Cleaning transfers older than {days_old} days (cutoff: {datetime.fromtimestamp(cutoff_time)})")
        
        # Clean up old transfer directories
        transfers_dir = os.path.join(self.data_dir, "transfers")
        if os.path.exists(transfers_dir):
            cleaned_count = 0
            for transfer_id in os.listdir(transfers_dir):
                transfer_path = os.path.join(transfers_dir, transfer_id)
                if os.path.isdir(transfer_path):
                    try:
                        # Check both creation time and modification time, use the older one
                        folder_ctime = os.path.getctime(transfer_path)
                        folder_mtime = os.path.getmtime(transfer_path)
                        folder_time = min(folder_ctime, folder_mtime)
                        
                        age_days = (time.time() - folder_time) / (24 * 60 * 60)
                        print(f"Transfer {transfer_id}: {age_days:.1f} days old (created: {datetime.fromtimestamp(folder_ctime)})")
                        
                        if folder_time < cutoff_time:
                            shutil.rmtree(transfer_path)
                            cleaned_count += 1
                            print(f"✅ Cleaned up old transfer: {transfer_id}")
                        else:
                            print(f"⏭️  Keeping recent transfer: {transfer_id}")
                    except Exception as e:
                        print(f"❌ Error cleaning old transfer {transfer_id}: {e}")
            
            print(f"Cleaned up {cleaned_count} old transfer directories")
          # Optionally clean up old database records (keep for history but mark as archived)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count old records
        cursor.execute('SELECT COUNT(*) FROM transfers WHERE timestamp < ?', (cutoff_time,))
        old_count = cursor.fetchone()[0]
        
        if old_count > 0:
            # Mark old records as archived instead of deleting them
            cursor.execute('''
                UPDATE transfers 
                SET status = 'archived' 
                WHERE timestamp < ? AND status != 'archived'
            ''', (cutoff_time,))
            
            conn.commit()
            print(f"Archived {old_count} old transfer records")
        
        conn.close()
    
    def auto_cleanup_on_transfer_complete(self, transfer_id, success):
        """Automatically clean up after a transfer completes"""
        if success:
            # For successful transfers, do NOT clean immediately
            # Transfer directories will be automatically cleaned after 24 hours
            # via the scheduled cleanup_old_transfers() method
            
            # NOTE: Do NOT clean temp files here for successful transfers
            # They are needed for verification/extraction in the main window
            # Temp files will be cleaned after processing is complete
            
            print(f"Transfer {transfer_id} completed successfully. Files will be auto-deleted after 24 hours.")
        else:
            # For failed transfers, clean immediately
            self.cleanup_completed_transfer(transfer_id)
            self.cleanup_temp_files()
            print(f"Auto-cleanup completed for failed transfer: {transfer_id}")
    
    def cleanup_specific_temp_file(self, filename):
        """Clean up a specific temp file after processing is complete"""
        temp_dir = os.path.join(self.data_dir, "temp")
        file_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned specific temp file: {filename}")
            except Exception as e:
                print(f"Error cleaning temp file {filename}: {e}")
    
    def cleanup_after_extraction(self, transfer_id, temp_filename):
        """Clean up temp files after successful extraction and verification"""
        # Clean the specific temp file that was processed
        self.cleanup_specific_temp_file(temp_filename)
        
        # Clean any remaining temp files from this transfer        self.cleanup_temp_files()
        
        print(f"Post-extraction cleanup completed for transfer: {transfer_id}")
    
    def startup_cleanup(self):
        """Perform cleanup operations when the application starts"""
        print("Performing startup cleanup...")
        
        # Clean all temp files on startup (they're from previous sessions)
        self.cleanup_temp_files()
        
        # Clean up old transfers (older than 1 day = 24 hours)
        self.cleanup_old_transfers(days_old=1)
        
        print("Startup cleanup completed")
    
    def shutdown_cleanup(self):
        """Perform cleanup operations when the application shuts down"""
        print("Performing shutdown cleanup...")
        
        # Clean temp directory
        self.cleanup_temp_files()
        
        # Clean up very old transfers (older than 30 days for shutdown cleanup)
        self.cleanup_old_transfers(days_old=30)
        
        print("Shutdown cleanup completed")
    
    def force_cleanup_all_transfers(self):
        """Force cleanup of ALL transfer directories regardless of age"""
        import shutil
        transfers_dir = os.path.join(self.data_dir, "transfers")
        
        if not os.path.exists(transfers_dir):
            print("No transfers directory found")
            return
        
        transfer_dirs = [d for d in os.listdir(transfers_dir) if os.path.isdir(os.path.join(transfers_dir, d))]
        
        if not transfer_dirs:
            print("No transfer directories found")
            return
        
        print(f"Found {len(transfer_dirs)} transfer directories to clean up")
        
        cleaned_count = 0
        for transfer_id in transfer_dirs:
            transfer_path = os.path.join(transfers_dir, transfer_id)
            try:
                shutil.rmtree(transfer_path)
                cleaned_count += 1
                print(f"✅ Cleaned up transfer: {transfer_id}")
            except Exception as e:
                print(f"❌ Error cleaning transfer {transfer_id}: {e}")
        
        print(f"Force cleanup completed: {cleaned_count}/{len(transfer_dirs)} directories cleaned")

