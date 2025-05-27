"""
Script to configure ngrok authtoken for SecureTransfer
"""

import os
import sys
import json

# Add the parent directory to sys.path to import from securetransfer
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from pyngrok import ngrok, conf
except ImportError:
    print("Error: pyngrok package not installed. Installing it now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok>=7.0.0"])
    try:
        from pyngrok import ngrok, conf
    except ImportError:
        print("Failed to install pyngrok. Please install it manually with: pip install pyngrok>=7.0.0")
        sys.exit(1)

try:
    from securetransfer.data.database import DatabaseManager
except ImportError:
    print("Error: securetransfer module not found. Make sure you're in the correct directory.")
    sys.exit(1)

def save_ngrok_authtoken(authtoken):
    """Save ngrok authtoken to the application settings"""
    try:
        # Use the database manager to handle settings
        db_manager = DatabaseManager()
        
        # Get current settings
        settings = db_manager.get_settings()
        
        # Add or update ngrok authtoken
        settings["ngrok_authtoken"] = authtoken
        
        # Save updated settings
        db_manager.update_settings(settings)
        
        # Configure ngrok immediately
        conf.get_default().auth_token = authtoken
        print(f"Successfully saved ngrok authtoken to settings")
        
        # Test ngrok configuration
        print("Testing ngrok configuration...")
        tunnels = ngrok.get_tunnels()
        print("Ngrok is properly configured!")
        return True
    
    except Exception as e:
        print(f"Error configuring ngrok: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ngrok_setup.py YOUR_AUTHTOKEN")
        sys.exit(1)
    
    authtoken = sys.argv[1]
    save_ngrok_authtoken(authtoken)
