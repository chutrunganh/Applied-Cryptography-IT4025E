"""
SecureTransfer - Help Dialogs
Provides help and about information to users
"""

import tkinter as tk
from tkinter import ttk


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


class UserGuideDialog:
    """Dialog showing user guide information"""
    
    def __init__(self, parent):
        """Initialize the user guide dialog"""
        self.parent = parent
        
        # Create UI
        self.dialog = None
        self.create_dialog()
    
    def create_dialog(self):
        """Create the dialog UI"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("SecureTransfer - User Guide")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=COLORS["primary"])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Container frame
        main_frame = tk.Frame(self.dialog, bg=COLORS["secondary"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title = tk.Label(main_frame, text="SecureTransfer User Guide", 
                       font=("Helvetica", 16, "bold"),
                       fg=COLORS["light"], bg=COLORS["secondary"])
        title.pack(pady=(0, 20))
        
        # Tab control for help sections
        tab_control = ttk.Notebook(main_frame)
        
        # Create tabs
        getting_started_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        sending_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        receiving_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        security_tab = tk.Frame(tab_control, bg=COLORS["secondary"])
        
        tab_control.add(getting_started_tab, text="Getting Started")
        tab_control.add(sending_tab, text="Sending Files")
        tab_control.add(receiving_tab, text="Receiving Files")
        tab_control.add(security_tab, text="Security")
        
        tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Populate tabs
        self.setup_getting_started_tab(getting_started_tab)
        self.setup_sending_tab(sending_tab)
        self.setup_receiving_tab(receiving_tab)
        self.setup_security_tab(security_tab)
        
        # Close button
        close_button = tk.Button(self.dialog, text="Close", command=self.dialog.destroy,
                              bg=COLORS["accent"], fg=COLORS["light"],
                              activebackground=COLORS["accent"], activeforeground=COLORS["light"],
                              font=("Helvetica", 10),
                              relief=tk.FLAT, padx=20, pady=8)
        close_button.pack(pady=(0, 15))
    
    def setup_getting_started_tab(self, parent):
        """Set up Getting Started tab content"""
        canvas = tk.Canvas(parent, bg=COLORS["secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        content_frame = tk.Frame(canvas, bg=COLORS["secondary"])
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Getting Started content
        sections = [
            ("Welcome to SecureTransfer", 
             "SecureTransfer is a secure peer-to-peer file sharing application that allows "
             "you to send files directly to other users without going through a central server. "
             "Your files are encrypted end-to-end for maximum security."),
            
            ("Creating an Account", 
             "1. Launch SecureTransfer\n"
             "2. Check the 'New User? Register' box\n"
             "3. Enter a username and password (at least 8 characters)\n"
             "4. Click 'Sign In' to register\n"
             "5. Log in with your new credentials"),
            
            ("User Interface Overview",
             "The main window is divided into three tabs:\n"
             "• Send Files: For sending files to other users\n"
             "• Receive Files: For receiving files from other users\n"
             "• Transfer History: View your past file transfers"),
            
            ("Configuring Settings",
             "1. Click on Options > Settings in the menu\n"
             "2. Configure your download directory, security options, and network settings\n"
             "3. Click Save to apply your changes")
        ]
        
        for i, (title, content) in enumerate(sections):
            section_title = tk.Label(content_frame, text=title, font=("Helvetica", 12, "bold"),
                                   fg=COLORS["light"], bg=COLORS["secondary"])
            section_title.grid(row=i*2, column=0, sticky="w", pady=(15, 5))
            
            section_content = tk.Label(content_frame, text=content, font=("Helvetica", 10),
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     justify=tk.LEFT, wraplength=500)
            section_content.grid(row=i*2+1, column=0, sticky="w", padx=(10, 0))
        
        # Configure canvas scrolling
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def setup_sending_tab(self, parent):
        """Set up Sending Files tab content"""
        canvas = tk.Canvas(parent, bg=COLORS["secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        content_frame = tk.Frame(canvas, bg=COLORS["secondary"])
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Sending Files content
        sections = [
            ("Sending Files Overview", 
             "SecureTransfer makes it easy to send files securely to other users. "
             "Files are split into chunks, encrypted, and digitally signed to ensure "
             "they arrive safely and unmodified."),
            
            ("How to Send a File", 
             "1. Go to the 'Send Files' tab\n"
             "2. Click 'Browse' and select the file you want to send\n"
             "3. Choose the connection type: Local Network, Direct Connection, or Ngrok Tunnel\n"
             "4. Set the port number (default is 5000)\n"
             "5. Click 'Start Server' to begin\n"
             "6. Share the displayed connection information with the recipient\n"
             "7. Wait for the recipient to connect and download the file"),
              ("Connection Types",
             "• Local Network: Best for sending files to users on the same network\n"
             "• Direct Connection: Use when both you and the recipient have public IP addresses\n"
             "• Ngrok Tunnel: Best option when behind firewalls or NAT (requires Ngrok account)\n\n"
             "  Note: With Ngrok, the URL displayed will be HTTP format. When receiving,\n"
             "  the recipient should enter just the hostname without http:// prefix."),
            
            ("Transfer Status",
             "The progress bar and status messages will keep you updated on the transfer status. "
             "When the transfer is complete, you'll see a success message and the transfer "
             "will be recorded in your transfer history.")
        ]
        
        for i, (title, content) in enumerate(sections):
            section_title = tk.Label(content_frame, text=title, font=("Helvetica", 12, "bold"),
                                   fg=COLORS["light"], bg=COLORS["secondary"])
            section_title.grid(row=i*2, column=0, sticky="w", pady=(15, 5))
            
            section_content = tk.Label(content_frame, text=content, font=("Helvetica", 10),
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     justify=tk.LEFT, wraplength=500)
            section_content.grid(row=i*2+1, column=0, sticky="w", padx=(10, 0))
        
        # Configure canvas scrolling
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def setup_receiving_tab(self, parent):
        """Set up Receiving Files tab content"""
        canvas = tk.Canvas(parent, bg=COLORS["secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        content_frame = tk.Frame(canvas, bg=COLORS["secondary"])
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Receiving Files content
        sections = [
            ("Receiving Files Overview", 
             "SecureTransfer makes it easy to receive files from other users. "
             "All incoming files are verified with digital signatures and decrypted "
             "automatically."),
            
            ("How to Receive a File", 
             "1. Go to the 'Receive Files' tab\n"
             "2. Enter the connection information provided by the sender\n"
             "3. Click 'Connect' to establish a connection\n"
             "4. Once connected, the file details will be displayed\n"
             "5. Click 'Accept' to start downloading the file\n"
             "6. The file will be saved to your download directory"),
            
            ("Connection Information",
             "To connect to a sender, you'll need:\n"
             "• IP Address: The sender's IP address or hostname\n"
             "• Port: The port number the sender is using (default is 5000)\n"
             "• Connection Type: Must match the sender's connection type"),
            
            ("Verifying Transfers",
             "SecureTransfer automatically verifies:\n"
             "• File integrity using checksums\n"
             "• Sender identity using digital signatures\n"
             "• Decryption using your private key\n\n"
             "If any verification fails, you'll be notified and the file will be rejected.")
        ]
        
        for i, (title, content) in enumerate(sections):
            section_title = tk.Label(content_frame, text=title, font=("Helvetica", 12, "bold"),
                                   fg=COLORS["light"], bg=COLORS["secondary"])
            section_title.grid(row=i*2, column=0, sticky="w", pady=(15, 5))
            
            section_content = tk.Label(content_frame, text=content, font=("Helvetica", 10),
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     justify=tk.LEFT, wraplength=500)
            section_content.grid(row=i*2+1, column=0, sticky="w", padx=(10, 0))
        
        # Configure canvas scrolling
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def setup_security_tab(self, parent):
        """Set up Security tab content"""
        canvas = tk.Canvas(parent, bg=COLORS["secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        content_frame = tk.Frame(canvas, bg=COLORS["secondary"])
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Security content
        sections = [
            ("Security Overview", 
             "SecureTransfer prioritizes your privacy and security with multiple layers of protection:"),
            
            ("End-to-End Encryption", 
             "All files are encrypted using Elliptic Curve Cryptography (ECC) with options for:\n"
             "• Medium: 256-bit keys\n"
             "• High: 384-bit keys (default)\n"
             "• Very High: 521-bit keys\n\n"
             "This ensures that only the intended recipient can decrypt and access your files."),
            
            ("Digital Signatures",
             "Every file is digitally signed, which:\n"
             "• Verifies the identity of the sender\n"
             "• Ensures the file hasn't been modified in transit\n"
             "• Prevents man-in-the-middle attacks"),
            
            ("Password Protection",
             "Your private keys are protected by your password. Choose a strong password "
             "that is at least 8 characters and includes a mix of letters, numbers, and "
             "special characters for maximum security."),
            
            ("Secure File Transfer",
             "Files are:\n"
             "• Split into chunks for efficient transfer\n"
             "• Each chunk is individually encrypted and verified\n"
             "• Checksums ensure complete file integrity\n"
             "• Transfer metadata is protected")
        ]
        
        for i, (title, content) in enumerate(sections):
            section_title = tk.Label(content_frame, text=title, font=("Helvetica", 12, "bold"),
                                   fg=COLORS["light"], bg=COLORS["secondary"])
            section_title.grid(row=i*2, column=0, sticky="w", pady=(15, 5))
            
            section_content = tk.Label(content_frame, text=content, font=("Helvetica", 10),
                                     fg=COLORS["light"], bg=COLORS["secondary"],
                                     justify=tk.LEFT, wraplength=500)
            section_content.grid(row=i*2+1, column=0, sticky="w", padx=(10, 0))
        
        # Configure canvas scrolling
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))


class AboutDialog:
    """Dialog showing about information"""
    
    def __init__(self, parent):
        """Initialize the about dialog"""
        self.parent = parent
        
        # Create UI
        self.dialog = None
        self.create_dialog()
    
    def create_dialog(self):
        """Create the dialog UI"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("About SecureTransfer")
        self.dialog.geometry("400x350")
        self.dialog.configure(bg=COLORS["primary"])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Container frame
        main_frame = tk.Frame(self.dialog, bg=COLORS["secondary"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title = tk.Label(main_frame, text="SecureTransfer", 
                       font=("Helvetica", 20, "bold"),
                       fg=COLORS["accent"], bg=COLORS["secondary"])
        title.pack(pady=(0, 5))
        
        version = tk.Label(main_frame, text="Version 2.0", 
                         font=("Helvetica", 10),
                         fg=COLORS["muted"], bg=COLORS["secondary"])
        version.pack(pady=(0, 20))
        
        # Description
        description = tk.Label(main_frame, text=
                             "A secure peer-to-peer file sharing application with "
                             "end-to-end encryption, digital signatures, and "
                             "enhanced security features.",
                             font=("Helvetica", 10),
                             fg=COLORS["light"], bg=COLORS["secondary"],
                             justify=tk.CENTER, wraplength=300)
        description.pack(pady=(0, 20))
        
        # Features
        features_frame = tk.Frame(main_frame, bg=COLORS["secondary"])
        features_frame.pack(fill=tk.X)
        
        features = [
            "🔒 End-to-End Encryption",
            "📝 Digital Signatures",
            "📈 Large File Support",
            "🔄 Multiple Connection Types",
            "📱 Modern User Interface"
        ]
        
        for feature in features:
            feature_label = tk.Label(features_frame, text=feature, 
                                   font=("Helvetica", 10),
                                   fg=COLORS["light"], bg=COLORS["secondary"],
                                   justify=tk.LEFT)
            feature_label.pack(anchor=tk.W, pady=2)
          # Copyright
        copyright_label = tk.Label(main_frame, text="© 2025 SecureTransfer", 
                                 font=("Helvetica", 8),
                                 fg=COLORS["muted"], bg=COLORS["secondary"])
        copyright_label.pack(side=tk.BOTTOM, pady=(20, 0))
        
        # Close button
        close_button = tk.Button(self.dialog, text="Close", command=self.dialog.destroy,
                              bg=COLORS["accent"], fg=COLORS["light"],
                              activebackground=COLORS["accent"], activeforeground=COLORS["light"],
                              relief=tk.FLAT, padx=20, pady=8)
        close_button.pack(pady=(0, 15))
