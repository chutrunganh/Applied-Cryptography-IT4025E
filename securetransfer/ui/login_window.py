"""
SecureTransfer - Login Window
Implements the user authentication UI with modern styling
"""

import os
import json
import time
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
from ..core.encryption_manager import EncryptionManager, EncryptionStrength


# Color scheme
COLORS = {
    "primary": "#2c3e50",      # Dark blue
    "secondary": "#34495e",    # Slightly lighter blue
    "accent": "#3498db",       # Bright blue
    "success": "#2ecc71",      # Green
    "warning": "#f39c12",      # Orange
    "danger": "#e74c3c",       # Red
    "light": "#ecf0f1",        # Off-white
    "muted": "#bdc3c7"         # Light gray
}


def load_user_database():
    """Load the user database from a JSON file"""
    db_path = os.path.join("securetransfer", "data", "user_database.json")
    
    if not os.path.exists(db_path):
        return {}
        
    with open(db_path, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_user_database(user_db):
    """Save the user database to a JSON file"""
    db_path = os.path.join("securetransfer", "data", "user_database.json")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    with open(db_path, "w") as f:
        json.dump(user_db, f, indent=2)


def hash_password(password):
    """Create a SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    """Register a new user with username and password"""
    user_db = load_user_database()
    
    if username in user_db:
        return False  # Username already exists
        
    # Store hashed password - never store plain passwords
    user_db[username] = {
        "password_hash": hash_password(password),
        "created_at": time.time(),
        "last_login": None,
        "key_strength": EncryptionStrength.HIGH  # Default to high security
    }
    
    save_user_database(user_db)
    
    # Create user-specific key directory
    user_keys_dir = os.path.join("securetransfer", "data", "users", username, "keys")
    os.makedirs(user_keys_dir, exist_ok=True)
    
    # Generate keys for the new user
    encryption_mgr = EncryptionManager(password, username)
    
    return True


def validate_user(username, password):
    """Validate a user's credentials and update last login"""
    user_db = load_user_database()
    
    if username not in user_db:
        return False
        
    if user_db[username]["password_hash"] == hash_password(password):
        # Update last login time
        user_db[username]["last_login"] = time.time()
        save_user_database(user_db)
        return True
    
    return False


class LoginWindow:
    """Modern login window with username and password authentication"""
    
    def __init__(self, on_success_callback):
        """Initialize the login window and UI elements"""
        self.on_success = on_success_callback
        self.username = None
        self.password = None
        self.encryption_manager = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the login UI"""
        self.root = tk.Tk()
        self.root.title("SecureTransfer - Login")
        self.root.geometry("400x450")
        self.root.configure(bg=COLORS["primary"])
        
        # Application header
        header_frame = tk.Frame(self.root, bg=COLORS["primary"])
        header_frame.pack(fill=tk.X, pady=(20, 0))
        
        title = tk.Label(header_frame, text="SecureTransfer", font=("Helvetica", 22, "bold"),
                        fg=COLORS["light"], bg=COLORS["primary"])
        title.pack()
        
        subtitle = tk.Label(header_frame, text="Secure P2P File Sharing",
                          font=("Helvetica", 12), fg=COLORS["muted"], bg=COLORS["primary"])
        subtitle.pack(pady=(0, 20))
        
        # Login form
        form_frame = tk.Frame(self.root, bg=COLORS["secondary"],
                            padx=30, pady=30, highlightthickness=0)
        form_frame.pack(pady=20, padx=40, fill=tk.X)
        
        login_title = tk.Label(form_frame, text="Sign In", font=("Helvetica", 14, "bold"),
                             fg=COLORS["light"], bg=COLORS["secondary"])
        login_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Username field
        username_label = tk.Label(form_frame, text="Username", font=("Helvetica", 10),
                               fg=COLORS["light"], bg=COLORS["secondary"])
        username_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        self.username_entry = tk.Entry(form_frame, width=30, font=("Helvetica", 10),
                                    highlightthickness=0, relief=tk.FLAT, bd=5)
        self.username_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
          # Password field
        password_label = tk.Label(form_frame, text="Password (min. 4 characters)", font=("Helvetica", 10),
                               fg=COLORS["light"], bg=COLORS["secondary"])
        password_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(form_frame, width=30, font=("Helvetica", 10),
                                    show="●", highlightthickness=0, relief=tk.FLAT, bd=5)
        self.password_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))
          # Register checkbox
        self.register_var = tk.BooleanVar()
        register_cb = tk.Checkbutton(form_frame, text="New User? Register", variable=self.register_var,
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"],
                                  command=self.toggle_registration_mode)
        register_cb.grid(row=5, column=0, sticky="w", pady=(0, 15))
          # Login button
        login_button = tk.Button(form_frame, text="Sign In", command=self.handle_login,
                              bg=COLORS["accent"], fg=COLORS["light"],
                              activebackground=COLORS["accent"], activeforeground=COLORS["light"],
                              font=("Helvetica", 10, "bold"),
                              relief=tk.FLAT, padx=20, pady=8)
        login_button.grid(row=6, column=0, sticky="w")
        print("Login button created with handle_login command binding")
        
        # Status message
        self.status_var = tk.StringVar()
        status = tk.Label(self.root, textvariable=self.status_var,
                        fg=COLORS["muted"], bg=COLORS["primary"])
        status.pack(pady=(5, 0))
        
        # Footer
        footer = tk.Label(self.root, text="© 2023 SecureTransfer",
                        font=("Helvetica", 8), fg=COLORS["muted"], bg=COLORS["primary"])
        footer.pack(side=tk.BOTTOM, pady=10)
        
        # Set default focus
        self.username_entry.focus_set()
          # Bind Enter key
        self.root.bind('<Return>', lambda event: self.handle_login())
    
    def handle_login(self):
        """Process login or registration attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        print(f"Login attempt - Username: {username}, Password: {'*' * len(password)}")
        
        if not username:
            self.status_var.set("Username is required")
            self.username_entry.focus_set()
            print("Username required")
            return
            
        if not password:
            self.status_var.set("Password is required")
            self.password_entry.focus_set()
            print("Password required")
            return
          # Registration mode
        if self.register_var.get():
            if len(password) < 4:  # Reduced from 8 to 4 characters
                self.status_var.set("Password must be at least 4 characters")
                print("Password too short for registration")
                return
                
            if register_user(username, password):
                messagebox.showinfo("Success", "Registration successful. You may now log in.")
                self.register_var.set(False)
                self.status_var.set("Registration successful. Please sign in.")
                print("Registration successful")
                return
            else:
                self.status_var.set("Username already exists")
                print("Username already exists")
                return
                
        # Login mode
        else:
            print(f"Attempting to validate user {username}")
            if validate_user(username, password):
                print("User validated successfully")
                self.username = username
                self.password = password
                
                # Load encryption keys
                try:
                    print("Creating encryption manager")
                    self.encryption_manager = EncryptionManager(password, username)
                    print("Loading keys")
                    keys = self.encryption_manager.load_keys()
                    
                    if keys:
                        print("Keys loaded successfully")
                        self.status_var.set("Login successful. Loading...")
                        self.root.update()
                        self.root.destroy()
                        
                        print("Calling success callback")
                        # Call the success callback
                        self.on_success(username, self.encryption_manager)
                    else:
                        print("Failed to load keys")
                        self.status_var.set("Failed to load encryption keys")
                except Exception as e:
                    print(f"Exception during key loading: {e}")
                    self.status_var.set(f"Error: {e}")
                
            else:
                print("Invalid username or password")
                self.status_var.set("Invalid username or password")
    
    def toggle_registration_mode(self):
        """Show or hide registration-specific instructions"""
        if self.register_var.get():
            self.status_var.set("For registration: password must be at least 4 characters")
        else:
            self.status_var.set("")
    
    def run(self):
        """Start the login window event loop"""
        self.root.mainloop()
