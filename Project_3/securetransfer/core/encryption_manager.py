"""
SecureTransfer - Encryption Manager
"""
import os
import uuid
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes


class EncryptionStrength:
    MEDIUM = "SECP256R1"
    HIGH = "SECP384R1"
    VERY_HIGH = "SECP521R1"


def public_encode_to_string(public_key):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def public_decode_from_string(pem_str):
    return serialization.load_pem_public_key(pem_str.encode('utf-8'))


class EncryptionManager:
    def __init__(self, password, username=None, key_strength=EncryptionStrength.HIGH):
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
        try:
            print(f"Creating new key pair with strength {self.key_strength}")
            os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
            
            curve = getattr(ec, self.key_strength)()
            self.private_key = ec.generate_private_key(curve)
            
            # Save the private key (encrypted with password)
            with open(self.private_key_path, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(self.password)
                ))
            
            # Save the public key
            self.public_key = self.private_key.public_key()
            with open(self.public_key_path, "wb") as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            print("Key pair created and saved successfully")
        except Exception as e:
            print(f"Error creating keys: {e}")
    
    def load_keys(self):
        try:
            with open(self.private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=self.password
                )
            
            with open(self.public_key_path, "rb") as f:
                self.public_key = serialization.load_pem_public_key(f.read())
            
            return [self.private_key, self.public_key]
        except Exception as e:
            print(f"Failed to load keys: {e}")
            return None

    def encrypt_file(self, source_path, recipient_public_key):
        # Implementation simplified for fix
        pass
    
    def decrypt_file(self, encrypted_path, output_path=None):
        # Implementation simplified for fix
        pass
