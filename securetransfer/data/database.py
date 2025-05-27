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

