"""
SecureTransfer - Encryption Manager
Handles key generation, storage, and encryption/decryption operations
"""

import os
import uuid
import base64
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionStrength:
    MEDIUM = "SECP256R1"
    HIGH = "SECP384R1"
    VERY_HIGH = "SECP521R1"


def public_encode_to_string(public_key):
    """Convert a public key object to PEM string format"""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def public_decode_from_string(pem_str):
    """Convert a PEM string back to a public key object"""
    return serialization.load_pem_public_key(pem_str.encode('utf-8'))


class EncryptionManager:
    """Enhanced encryption management with support for multiple key strengths"""
    
    def __init__(self, password, username=None, key_strength=EncryptionStrength.HIGH):
        """Initialize with password and optional username for multi-user support"""
        self.password = password.encode()
        self.username = username
        self.key_strength = key_strength
        self.private_key = None
        self.public_key = None
        
        # Determine the key directory based on username
        if username:
            self.key_dir = os.path.join("securetransfer", "data", "users", username, "keys")
            os.makedirs(self.key_dir, exist_ok=True)
        else:
            self.key_dir = os.path.join("securetransfer", "data")
            os.makedirs(self.key_dir, exist_ok=True)
            
        self.private_key_path = os.path.join(self.key_dir, "private_key.pem")
        self.public_key_path = os.path.join(self.key_dir, "public_key.pem")
          # Create keys if they don't exist
        if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
            self._create_keys()
    
    def _create_keys(self):
        """Generate new ECC key pair with the selected strength"""
        try:
            print(f"Creating new key pair with strength {self.key_strength}")
            
            # Make sure the directory exists
            import os
            os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
            
            curve = getattr(ec, self.key_strength)()
            self.private_key = ec.generate_private_key(curve)
            
            # Save the private key (encrypted with password)
            print(f"Saving private key to {self.private_key_path}")
            with open(self.private_key_path, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(self.password)
                ))
            
            # Save the public key
            self.public_key = self.private_key.public_key()
            print(f"Saving public key to {self.public_key_path}")
            with open(self.public_key_path, "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))            print("Key pair created and saved successfully")
        except Exception as e:
            print(f"Error creating keys: {e}")
            import traceback
            traceback.print_exc()
    
    def load_keys(self):
        """Load existing keys from storage"""
        try:
            print(f"Loading private key from {self.private_key_path}")
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=self.password
                )
            print("Private key loaded successfully")
            
            print(f"Loading public key from {self.public_key_path}")
            with open(self.public_key_path, "rb") as f:
                self.public_key = serialization.load_pem_public_key(f.read())
            print("Public key loaded successfully")
            
            return [self.private_key, self.public_key]
        except FileNotFoundError as e:
            print(f"Keys not found: {e} - Will attempt to create new keys")
            self._create_keys()
            return self.load_keys()
        except Exception as e:
            print(f"Failed to load keys: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def encrypt_file(self, source_path, recipient_public_key):
        """
        Encrypt a file for a specific recipient using their public key
        Returns the path to the encrypted file
        """
        # Generate a random AES key for file encryption
        session_key = os.urandom(32)  # 256-bit key for AES-256
        
        # Encrypt the session key with recipient's public key
        encrypted_key = recipient_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Generate random IV for AES
        iv = os.urandom(16)
        
        # Create encrypted output file path
        file_id = str(uuid.uuid4())[:8]
        encrypted_path = f"{source_path}.{file_id}.encrypted"
        
        # Read the source file and encrypt it
        with open(source_path, 'rb') as in_file, open(encrypted_path, 'wb') as out_file:
            # Write IV and encrypted key length and data
            out_file.write(iv)
            out_file.write(len(encrypted_key).to_bytes(2, byteorder='big'))
            out_file.write(encrypted_key)
            
            # Create AES cipher
            cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
            encryptor = cipher.encryptor()
            
            # Process file in chunks
            while True:
                chunk = in_file.read(64 * 1024)  # 64KB chunks
                if not chunk:
                    break
                out_file.write(encryptor.update(chunk))
                
            # Finalize encryption
            out_file.write(encryptor.finalize())
            
        return encrypted_path
    
    def decrypt_file(self, encrypted_path, output_path=None):
        """
        Decrypt a file that was encrypted for us
        Returns the path to the decrypted file
        """
        if not output_path:
            # Generate output path by removing .encrypted extension
            if encrypted_path.endswith('.encrypted'):
                output_path = encrypted_path[:-10]
            else:
                base, ext = os.path.splitext(encrypted_path)
                output_path = f"{base}_decrypted{ext}"
        
        with open(encrypted_path, 'rb') as in_file:
            # Read IV (16 bytes) and encrypted session key
            iv = in_file.read(16)
            key_length = int.from_bytes(in_file.read(2), byteorder='big')
            encrypted_key = in_file.read(key_length)
            
            # Decrypt the session key using our private key
            session_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Create AES cipher for decryption
            cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv))
            decryptor = cipher.decryptor()
            
            with open(output_path, 'wb') as out_file:
                # Process file in chunks
                while True:
                    chunk = in_file.read(64 * 1024)  # 64KB chunks
                    if not chunk:
                        break
                    out_file.write(decryptor.update(chunk))
                
                # Finalize decryption
                out_file.write(decryptor.finalize())
                
        return output_path
