"""
SecureTransfer - Settings Dialog
Provides a UI for configuring application settings
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..core.encryption_manager import EncryptionStrength
from ..core.digital_signature import SignatureAlgorithm
from ..data.database import DatabaseManager


# Color scheme (same as main app)
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


class SettingsDialog:
    """Settings dialog for configuring application preferences"""
    
    def __init__(self, parent):
        """Initialize the settings dialog"""
        self.parent = parent
        self.db_manager = DatabaseManager()
        self.settings = self.db_manager.get_settings()
        
        # Create UI elements
        self.dialog = None
        self.create_dialog()
    
    def create_dialog(self):
        """Create the settings dialog UI"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("SecureTransfer Settings")
        self.dialog.geometry("550x600")
        self.dialog.configure(bg=COLORS["primary"])
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Tab control for settings categories
        tab_control = ttk.Notebook(self.dialog)
        
        # General settings tab
        general_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        security_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        network_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        appearance_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        
        tab_control.add(general_tab, text="General")
        tab_control.add(security_tab, text="Security")
        tab_control.add(network_tab, text="Network")
        tab_control.add(appearance_tab, text="Appearance")
        
        tab_control.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)
        
        # Set up each tab
        self.setup_general_tab(general_tab)
        self.setup_security_tab(security_tab)
        self.setup_network_tab(network_tab)
        self.setup_appearance_tab(appearance_tab)
        
        # Bottom buttons
        button_frame = tk.Frame(self.dialog, bg=COLORS["primary"])
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        save_button = tk.Button(button_frame, text="Save", command=self.save_settings,
                             bg=COLORS["accent"], fg=COLORS["light"],
                             activebackground=COLORS["accent"], activeforeground=COLORS["light"],
                             font=("Helvetica", 10, "bold"),
                             relief=tk.FLAT, padx=20, pady=8)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                               bg=COLORS["secondary"], fg=COLORS["light"],
                               activebackground=COLORS["secondary"], activeforeground=COLORS["light"],
                               relief=tk.FLAT, padx=20, pady=8)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def setup_general_tab(self, parent):
        """Set up the General settings tab"""
        frame = tk.Frame(parent, bg=COLORS["secondary"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Download directory
        tk.Label(frame, text="Download Directory", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=0, column=0, sticky="w", pady=(0, 5))
        
        dir_frame = tk.Frame(frame, bg=COLORS["secondary"])
        dir_frame.grid(row=1, column=0, sticky="ew")
        
        self.download_dir_var = tk.StringVar(value=self.settings.get("download_directory"))
        dir_entry = tk.Entry(dir_frame, textvariable=self.download_dir_var,
                          width=40, bg=COLORS["light"])
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = tk.Button(dir_frame, text="Browse", command=self.browse_directory,
                               bg=COLORS["accent"], fg=COLORS["light"],
                               activebackground=COLORS["accent"], activeforeground=COLORS["light"],
                               relief=tk.FLAT, padx=10, pady=2)
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Auto-accept transfers
        tk.Label(frame, text="Transfer Settings", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=2, column=0, sticky="w", pady=(20, 5))
        
        self.auto_accept_var = tk.BooleanVar(value=self.settings.get("auto_accept_transfers", False))
        auto_accept_cb = tk.Checkbutton(frame, text="Auto-accept incoming transfers",
                                     variable=self.auto_accept_var, 
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     selectcolor=COLORS["secondary"], 
                                     activebackground=COLORS["secondary"])
        auto_accept_cb.grid(row=3, column=0, sticky="w")
        
        self.notify_var = tk.BooleanVar(value=self.settings.get("notify_on_complete", True))
        notify_cb = tk.Checkbutton(frame, text="Notify when transfers complete",
                                variable=self.notify_var, 
                                fg=COLORS["light"], bg=COLORS["secondary"],
                                selectcolor=COLORS["secondary"], 
                                activebackground=COLORS["secondary"])
        notify_cb.grid(row=4, column=0, sticky="w")
        
        # Max concurrent transfers
        tk.Label(frame, text="Max concurrent transfers:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=5, column=0, sticky="w", pady=(10, 0))
        
        self.max_transfers_var = tk.StringVar(value=str(self.settings.get("max_concurrent_transfers", 3)))
        max_transfers = tk.Spinbox(frame, from_=1, to=10, textvariable=self.max_transfers_var,
                                width=5, bg=COLORS["light"])
        max_transfers.grid(row=5, column=0, sticky="e")
    
    def setup_security_tab(self, parent):
        """Set up the Security settings tab"""
        frame = tk.Frame(parent, bg=COLORS["secondary"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Encryption strength
        tk.Label(frame, text="Encryption Settings", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=0, column=0, sticky="w", pady=(0, 10), columnspan=2)
                   
        tk.Label(frame, text="Encryption Strength:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        self.encryption_var = tk.StringVar(value=self.settings.get("encryption_strength", "HIGH"))
        enc_frame = tk.Frame(frame, bg=COLORS["secondary"])
        enc_frame.grid(row=2, column=0, sticky="w", pady=(0, 10), columnspan=2)
        
        enc_medium = tk.Radiobutton(enc_frame, text="Medium (256-bit)", variable=self.encryption_var,
                                  value=EncryptionStrength.MEDIUM, 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        enc_medium.pack(anchor=tk.W)
        
        enc_high = tk.Radiobutton(enc_frame, text="High (384-bit)", variable=self.encryption_var,
                                value=EncryptionStrength.HIGH, 
                                fg=COLORS["light"], bg=COLORS["secondary"],
                                selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        enc_high.pack(anchor=tk.W)
        
        enc_very_high = tk.Radiobutton(enc_frame, text="Very High (521-bit)", variable=self.encryption_var,
                                     value=EncryptionStrength.VERY_HIGH, 
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        enc_very_high.pack(anchor=tk.W)
        
        # Signature algorithm
        tk.Label(frame, text="Signature Algorithm:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=3, column=0, sticky="w", pady=(10, 5))
        
        self.signature_var = tk.StringVar(value="SHA256")
        sig_frame = tk.Frame(frame, bg=COLORS["secondary"])
        sig_frame.grid(row=4, column=0, sticky="w", pady=(0, 10), columnspan=2)
        
        sig_sha256 = tk.Radiobutton(sig_frame, text="SHA-256 (Faster)", variable=self.signature_var,
                                  value="SHA256", 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        sig_sha256.pack(anchor=tk.W)
        
        sig_sha512 = tk.Radiobutton(sig_frame, text="SHA-512 (More Secure)", variable=self.signature_var,
                                  value="SHA512", 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        sig_sha512.pack(anchor=tk.W)
        
        # Chunk size
        tk.Label(frame, text="File Chunk Size:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=5, column=0, sticky="w", pady=(10, 5))
        
        chunk_frame = tk.Frame(frame, bg=COLORS["secondary"])
        chunk_frame.grid(row=6, column=0, sticky="w", columnspan=2)
        
        self.chunk_size_var = tk.IntVar(value=self.settings.get("chunk_size", 2*1024*1024) // (1024*1024))
        chunk_sizes = [1, 2, 4, 8, 16]
        
        for i, size in enumerate(chunk_sizes):
            chunk_radio = tk.Radiobutton(chunk_frame, text=f"{size} MB", variable=self.chunk_size_var,
                                      value=size, 
                                      fg=COLORS["light"], bg=COLORS["secondary"],
                                      selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
            chunk_radio.pack(anchor=tk.W)
    
    def setup_network_tab(self, parent):
        """Set up the Network settings tab"""
        frame = tk.Frame(parent, bg=COLORS["secondary"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Default port
        tk.Label(frame, text="Connection Settings", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=0, column=0, sticky="w", pady=(0, 10), columnspan=2)
                   
        tk.Label(frame, text="Default Port:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=1, column=0, sticky="w")
        
        self.port_var = tk.StringVar(value=str(self.settings.get("default_port", 5000)))
        port_entry = tk.Entry(frame, textvariable=self.port_var, width=10,
                           bg=COLORS["light"])
        port_entry.grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Default connection type
        tk.Label(frame, text="Default Connection Type:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=2, column=0, sticky="w", pady=(15, 5))
        
        self.conn_type_var = tk.StringVar(value=self.settings.get("default_connection_type", "local"))
        conn_frame = tk.Frame(frame, bg=COLORS["secondary"])
        conn_frame.grid(row=3, column=0, sticky="w", pady=(0, 10), columnspan=2)
        
        conn_local = tk.Radiobutton(conn_frame, text="Local Network", variable=self.conn_type_var,
                                  value="local", 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        conn_local.pack(anchor=tk.W)
        
        conn_direct = tk.Radiobutton(conn_frame, text="Direct Connection", variable=self.conn_type_var,
                                   value="direct", 
                                   fg=COLORS["light"], bg=COLORS["secondary"],
                                   selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        conn_direct.pack(anchor=tk.W)
        
        conn_ngrok = tk.Radiobutton(conn_frame, text="Ngrok Tunnel", variable=self.conn_type_var,
                                  value="ngrok", 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        conn_ngrok.pack(anchor=tk.W)
        
        # Ngrok settings (if available)
        tk.Label(frame, text="Ngrok Settings", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=4, column=0, sticky="w", pady=(20, 10), columnspan=2)
                   
        tk.Label(frame, text="Ngrok Auth Token:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=5, column=0, sticky="w")
        
        self.ngrok_token_var = tk.StringVar(value=self.settings.get("ngrok_auth_token", ""))
        ngrok_token_entry = tk.Entry(frame, textvariable=self.ngrok_token_var, width=30,
                                  bg=COLORS["light"])
        ngrok_token_entry.grid(row=5, column=1, sticky="w", padx=(10, 0))
        
        # Set ngrok region
        tk.Label(frame, text="Ngrok Region:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=6, column=0, sticky="w", pady=(10, 0))
        
        self.ngrok_region_var = tk.StringVar(value=self.settings.get("ngrok_region", "us"))
        regions = ["us", "eu", "ap", "au", "sa", "jp", "in"]
        region_dropdown = ttk.Combobox(frame, textvariable=self.ngrok_region_var,
                                     values=regions, width=10)
        region_dropdown.grid(row=6, column=1, sticky="w", padx=(10, 0), pady=(10, 0))
    
    def setup_appearance_tab(self, parent):
        """Set up the Appearance settings tab"""
        frame = tk.Frame(parent, bg=COLORS["secondary"], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Theme selection
        tk.Label(frame, text="Theme", fg=COLORS["light"], 
               bg=COLORS["secondary"], font=("Helvetica", 10, "bold")).grid(
                   row=0, column=0, sticky="w", pady=(0, 10), columnspan=2)
        
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        theme_frame = tk.Frame(frame, bg=COLORS["secondary"])
        theme_frame.grid(row=1, column=0, sticky="w", pady=(0, 20), columnspan=2)
        
        theme_dark = tk.Radiobutton(theme_frame, text="Dark Theme", variable=self.theme_var,
                                  value="dark", 
                                  fg=COLORS["light"], bg=COLORS["secondary"],
                                  selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        theme_dark.pack(anchor=tk.W)
        
        theme_light = tk.Radiobutton(theme_frame, text="Light Theme", variable=self.theme_var,
                                   value="light", 
                                   fg=COLORS["light"], bg=COLORS["secondary"],
                                   selectcolor=COLORS["secondary"], activebackground=COLORS["secondary"])
        theme_light.pack(anchor=tk.W)
        
        # Font size
        tk.Label(frame, text="Font Size:", fg=COLORS["light"], 
               bg=COLORS["secondary"]).grid(row=2, column=0, sticky="w")
        
        self.font_size_var = tk.IntVar(value=self.settings.get("font_size", 10))
        font_size = tk.Spinbox(frame, from_=8, to=16, textvariable=self.font_size_var,
                            width=5, bg=COLORS["light"])
        font_size.grid(row=2, column=1, sticky="w", padx=(10, 0))
        
        # Reset theme button
        reset_button = tk.Button(frame, text="Reset to Default Theme", command=self.reset_theme,
                              bg=COLORS["muted"], fg=COLORS["light"],
                              activebackground=COLORS["muted"], activeforeground=COLORS["light"],
                              relief=tk.FLAT, padx=10, pady=5)
        reset_button.grid(row=3, column=0, sticky="w", pady=(20, 0))
    
    def browse_directory(self):
        """Open a directory browser dialog"""
        directory = filedialog.askdirectory(
            initialdir=self.download_dir_var.get(),
            title="Select Download Directory"
        )
        
        if directory:  # If user didn't cancel
            self.download_dir_var.set(directory)
    
    def reset_theme(self):
        """Reset theme settings to default"""
        self.theme_var.set("dark")
        self.font_size_var.set(10)
    
    def save_settings(self):
        """Save all settings"""
        new_settings = {
            "download_directory": self.download_dir_var.get(),
            "default_port": int(self.port_var.get()),
            "default_connection_type": self.conn_type_var.get(),
            "encryption_strength": self.encryption_var.get(),
            "signature_algorithm": self.signature_var.get(),
            "theme": self.theme_var.get(),
            "auto_accept_transfers": self.auto_accept_var.get(),
            "notify_on_complete": self.notify_var.get(),
            "max_concurrent_transfers": int(self.max_transfers_var.get()),
            "chunk_size": int(self.chunk_size_var.get()) * 1024 * 1024,  # Convert MB to bytes
            "ngrok_auth_token": self.ngrok_token_var.get(),
            "ngrok_region": self.ngrok_region_var.get(),
            "font_size": self.font_size_var.get()
        }
        
        try:
            # Create download directory if it doesn't exist
            os.makedirs(new_settings["download_directory"], exist_ok=True)
            
            # Save settings
            self.db_manager.update_settings(new_settings)
            messagebox.showinfo("Success", "Settings saved successfully")
            self.dialog.destroy()
              # Notify parent that settings have changed
            if hasattr(self.parent, "on_settings_changed"):
                self.parent.on_settings_changed(new_settings)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

