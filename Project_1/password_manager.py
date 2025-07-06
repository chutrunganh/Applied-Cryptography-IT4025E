import os
import base64
import json
import hmac as hmac_module
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional, Tuple, Dict, Any

class Keychain:
    def __init__(self, master_password, salt=None, kv_store=None):
        """
        # This initializes the password manager with a master password
        # - If no salt is provided, we generate a random one for key derivation
        # - The key-value store (kv_store) holds the encrypted passwords
        # - We derive a master key from the password, then create sub-keys for different purposes
        """
        # If no salt is provided, generate a new one
        self.salt = salt if salt is not None else os.urandom(16)
        
        # Initialize the key-value store
        self.kv_store = {} if kv_store is None else kv_store
        
        # Generate the master key and sub-keys
        self.master_key = self._derive_master_key(master_password)
        self.hmac_key, self.encryption_key = self._derive_sub_keys(self.master_key)
    
    @staticmethod
    def new(keychain_password):
        """
        # Convenience method to create a new password manager
        # Simply calls the constructor with just a master password
        """
        return Keychain(keychain_password)
    
    @staticmethod
    def load(keychain_password, repr_str, trusted_data_check=None):
        """
        # Loads an existing password manager from its serialized string
        # - Verifies integrity with trusted_data_check (optional SHA-256 hash)
        # - Reconstructs the keychain with the original salt
        # - Verifies domain tags to prevent swap attacks
        # - Will raise errors if tampering is detected
        """
        try:
            data = json.loads(repr_str)
            
            # Check if required fields exist
            if 'salt' not in data or 'kvs' not in data:
                raise ValueError("Invalid keychain format")
            
            # Decode the salt
            salt = base64.b64decode(data['salt'])
            
            # Create password manager with the provided salt and empty KVS
            pm = Keychain(keychain_password, salt=salt)
            
            # Verify the integrity of the data if trusted_data_check is provided
            if trusted_data_check is not None:
                # Compute the hash of the serialized data
                current_hash = Keychain._compute_hash(repr_str)
                if current_hash != trusted_data_check:
                    raise ValueError("Integrity check failed: data may have been tampered with")
            
            # Load the KVS entries
            for domain_hmac, encrypted_data in data['kvs'].items():
                # The domain HMAC is already a string (base64 encoded)
                # The encrypted data needs to be parsed
                nonce = base64.b64decode(encrypted_data['nonce'])
                ciphertext = base64.b64decode(encrypted_data['ciphertext'])
                domain_tag = base64.b64decode(encrypted_data['domain_tag']) if 'domain_tag' in encrypted_data else None
                
                # Verify the domain tag to prevent swap attacks
                if domain_tag is None:
                    raise ValueError("Missing domain tag")
                
                # Verify that the domain_hmac matches the tag
                # Fix the HMAC constructor by explicitly passing the digestmod parameter
                h = hmac_module.new(key=pm.hmac_key, msg=domain_hmac.encode('utf-8'), digestmod='sha256')
                computed_domain_tag = h.digest()
                
                if not hmac_module.compare_digest(domain_tag, computed_domain_tag):
                    raise ValueError("Swap attack detected: domain hash verification failed")
                
                # Store the encrypted data in the KVS
                pm.kv_store[domain_hmac] = {
                    'nonce': nonce,
                    'ciphertext': ciphertext,
                    'domain_tag': domain_tag
                }
                
            return pm
            
        except Exception as e:
            raise ValueError(f"Failed to load keychain: {str(e)}")
    
    def dump(self):
        """
        # Serializes the password manager to a string format
        # - Encodes the salt and all encrypted entries to base64
        # - Returns both the serialized string and its hash for integrity checking
        """
        # Create a dictionary with the salt and KVS
        data = {
            'salt': base64.b64encode(self.salt).decode('utf-8'),
            'kvs': {}
        }
        
        # Add each entry in the KVS to the serialized data
        for domain_hmac, encrypted_data in self.kv_store.items():
            data['kvs'][domain_hmac] = {
                'nonce': base64.b64encode(encrypted_data['nonce']).decode('utf-8'),
                'ciphertext': base64.b64encode(encrypted_data['ciphertext']).decode('utf-8'),
                'domain_tag': base64.b64encode(encrypted_data['domain_tag']).decode('utf-8')
            }
        
        # Serialize to JSON
        serialized = json.dumps(data)
        
        # Compute the hash
        hash_value = self._compute_hash(serialized)
        
        return serialized, hash_value
    
    @staticmethod
    def _compute_hash(data):
        """
        # Utility function to compute SHA-256 hash of a string
        # Used for integrity verification
        """
        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(data.encode('utf-8'))
        return hasher.finalize()
    
    def _derive_master_key(self, master_password):
        """
        # Uses PBKDF2 to derive a strong key from the master password
        # - Salt prevents rainbow table attacks
        # - High iteration count (100,000) makes brute-force attacks expensive
        """
        # Use PBKDF2 to derive a master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits key
            salt=self.salt,
            iterations=100000,  # High number of iterations makes brute-forcing harder
        )
        
        master_key = kdf.derive(master_password.encode('utf-8'))
        return master_key
    
    def _derive_sub_keys(self, master_key):
        """
        # Creates two separate keys from the master key:
        # 1. HMAC key - used for domain name hashing and integrity checks
        # 2. Encryption key - used for password encryption/decryption
        # This follows the principle of key separation for different purposes
        """
        # Create two different HMAC keys for different purposes
        h1 = hmac.HMAC(master_key, hashes.SHA256())
        h1.update(b"HMAC_KEY_PURPOSE")
        hmac_key = h1.finalize()
        
        h2 = hmac.HMAC(master_key, hashes.SHA256())
        h2.update(b"ENCRYPTION_KEY_PURPOSE")
        encryption_key = h2.finalize()
        
        return hmac_key, encryption_key
    
    def _compute_domain_hmac(self, domain):
        """
        # Creates a secure hash (HMAC) of the domain name
        # This serves as the key in our key-value store
        # Using HMAC prevents attackers from guessing domain entries
        """
        h = hmac.HMAC(self.hmac_key, hashes.SHA256())
        h.update(domain.encode('utf-8'))
        domain_hmac = h.finalize()
        return base64.b64encode(domain_hmac).decode('utf-8')
    
    def _encrypt_password(self, password, domain_hmac):
        """
        # Encrypts a password using AES-GCM (authenticated encryption)
        # - Pads all passwords to 64 chars to prevent length leakage
        # - Uses a random nonce (never reused) for each encryption
        # - Binds the ciphertext to the domain to prevent swap attacks
        # - Creates a domain tag to verify domain-ciphertext binding
        """
        # Generate a random nonce
        nonce = os.urandom(12)  # 12 bytes is recommended for AES-GCM
        
        # Pad the password to prevent length leakage
        # Assume max length is 64 characters
        padded_password = password.ljust(64, '\0').encode('utf-8')
        
        # Encrypt the password
        aesgcm = AESGCM(self.encryption_key)
        # Use domain_hmac as associated data to bind the ciphertext to the domain
        ciphertext = aesgcm.encrypt(nonce, padded_password, domain_hmac.encode('utf-8'))
        
        # Create domain tag to prevent swap attacks
        # Fix: Use the correct way to create HMAC with built-in hmac module
        h = hmac_module.new(key=self.hmac_key, msg=domain_hmac.encode('utf-8'), digestmod='sha256')
        domain_tag = h.digest()
        
        # Return the encrypted data
        return {
            'nonce': nonce,
            'ciphertext': ciphertext,
            'domain_tag': domain_tag
        }
    
    def _decrypt_password(self, encrypted_data, domain_hmac):
        """
        # Decrypts a password using AES-GCM
        # - Verifies domain tag to prevent swap attacks
        # - Removes padding after decryption to get original password
        # - Will raise an error if tampering is detected
        """
        # Extract the required data
        nonce = encrypted_data['nonce']
        ciphertext = encrypted_data['ciphertext']
        
        # Verify the domain tag to prevent swap attacks
        domain_tag = encrypted_data['domain_tag']
        # Fix: Use the correct way to create HMAC with built-in hmac module
        h = hmac_module.new(key=self.hmac_key, msg=domain_hmac.encode('utf-8'), digestmod='sha256')
        computed_domain_tag = h.digest()
        
        if not hmac_module.compare_digest(domain_tag, computed_domain_tag):
            raise ValueError("Swap attack detected: domain hash verification failed")
        
        # Decrypt the password
        aesgcm = AESGCM(self.encryption_key)
        padded_plaintext = aesgcm.decrypt(nonce, ciphertext, domain_hmac.encode('utf-8'))
        
        # Remove padding
        plaintext = padded_plaintext.decode('utf-8').rstrip('\0')
        
        return plaintext
    
    def get(self, domain):
        """
        # Retrieves the password for a domain
        # - Computes the domain HMAC to look up the encrypted entry
        # - Returns None if the domain doesn't exist
        # - Handles decryption errors gracefully
        """
        # Compute the HMAC of the domain to use as a key
        domain_key = self._compute_domain_hmac(domain)
        
        # Get the encrypted password from the KVS
        encrypted_data = self.kv_store.get(domain_key)
        
        if encrypted_data is None:
            return None
        
        # Decrypt the password
        try:
            return self._decrypt_password(encrypted_data, domain_key)
        except Exception:
            return None
    
    def set(self, domain, password):
        """
        # Stores a password for a domain
        # - Computes the domain HMAC for lookup
        # - Encrypts the password with domain binding
        # - Saves the encrypted data in the key-value store
        """
        # Compute the HMAC of the domain to use as a key
        domain_key = self._compute_domain_hmac(domain)
        
        # Encrypt the password with domain binding
        encrypted_data = self._encrypt_password(password, domain_key)
        
        # Store the encrypted password in the KVS
        self.kv_store[domain_key] = encrypted_data
    
    def remove(self, domain):
        """
        # Removes a password for a domain
        # - Returns True if removed successfully
        # - Returns False if the domain didn't exist
        """
        # Compute the HMAC of the domain to use as a key
        domain_key = self._compute_domain_hmac(domain)
        
        # Remove the password from the KVS if it exists
        if domain_key in self.kv_store:
            del self.kv_store[domain_key]
            return True
        
        return False


# Example usage
if __name__ == "__main__":
    # Create a password manager with a master password
    manager = Keychain("my_secure_master_password")
    
    # Add some passwords
    manager.set("example.com", "password123")
    manager.set("github.com", "github_password")
    manager.set("google.com", "google_password")
    
    # Get a password
    print(manager.get("example.com"))  # Output: password123
    
    # Remove a password
    manager.remove("example.com")
    print(manager.get("example.com"))  # Output: None

