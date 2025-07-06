###############################################################################
# CS 255
# 1/12/25
# 
# messenger.py
# ______________
# Please implement the functions below according to the assignment spec
###############################################################################
from lib import (
    gen_random_salt,
    generate_eg,
    compute_dh,
    verify_with_ecdsa,
    hmac_to_aes_key,
    hmac_to_hmac_key,
    hkdf,
    encrypt_with_gcm,
    decrypt_with_gcm,
    gov_encryption_data_str
)
import json

class MessengerClient:
    def __init__(self, cert_authority_public_key: bytes, gov_public_key: bytes):
        """
        The certificate authority DSA public key is used to
        verify the authenticity and integrity of certificates
        of other users (see handout and receive_certificate)
        """
        # Feel free to store data as needed in the objects below
        # and modify their structure as you see fit.
        self.ca_public_key = cert_authority_public_key
        self.gov_public_key = gov_public_key
        self.conns = {}  # data for each active connection
        self.certs = {}  # certificates of other users
        self.my_certificate = None
        self.my_keys = None

    def generate_certificate(self, username: str) -> dict:
        """
        Generate a certificate to be stored with the certificate authority.
        The certificate must contain the field "username".
        Inputs:
            username: str
        Returns:
            certificate: dict
        """
        # Generate ElGamal key pair
        keys = generate_eg()
        
        # Create certificate with username and public key
        certificate = {
            "username": username,
            "public_key": keys["public"]
        }
        
        # Store my keys and certificate for future use
        self.my_keys = keys
        self.my_certificate = certificate
        
        return certificate

    def receive_certificate(self, certificate: dict, signature: bytes) -> None:
        """
        Receive and store another user's certificate.
        Inputs:
            certificate: dict
            signature: bytes
        Returns:
            None
        """
        # Verify the certificate signature using CA's public key
        valid = verify_with_ecdsa(self.ca_public_key, str(certificate), signature)
        
        if not valid:
            raise ValueError("Tampering detected!")
        
        # Store the certificate
        username = certificate["username"]
        self.certs[username] = certificate

    def send_message(self, name: str, plaintext: str) -> tuple[dict, tuple[bytes, bytes]]:
        """
        Generate the message to be sent to another user.
        Inputs:
            name: str
            plaintext: str
        Returns:
            (header, ciphertext): tuple(dict, tuple(bytes, bytes))
        """
        # Get recipient's certificate
        recipient_cert = self.certs.get(name)
        if not recipient_cert:
            raise ValueError(f"No certificate found for user {name}")
        
        # Check if we have an existing connection
        if name not in self.conns:
            # Initialize new connection
            self._initialize_sending_session(name)
        
        # Get current connection state
        conn = self.conns[name]
        
        # Check if we need to ratchet the DH keys
        if conn.get("need_ratchet", False):
            self._ratchet_dh_sending_keys(name)
        
        # Generate random IV for encryption
        receiver_iv = gen_random_salt()
        gov_iv = gen_random_salt()
        
        # Increment sending chain and get next sending key
        sending_key, conn["sending_chain_key"] = self._ratchet_sending_chain(conn["sending_chain_key"])
        
        # Convert sending key to AES key
        aes_sending_key = hmac_to_aes_key(sending_key, "encrypt")
        
        # Create header
        header = {
            "dh_public_key": conn["my_dh_public_key"],
            "prev_chain_length": conn.get("prev_chain_length", 0),
            "message_n": conn["message_n"],
            "receiver_iv": receiver_iv
        }
        
        # Encrypt sending key for government
        gov_key = compute_dh(self.my_keys["private"], self.gov_public_key)
        gov_key = hmac_to_aes_key(gov_key, gov_encryption_data_str)
        gov_ciphertext = encrypt_with_gcm(gov_key, aes_sending_key, gov_iv)
        
        # Add government encryption data to header
        header["v_gov"] = self.my_keys["public"]
        header["c_gov"] = gov_ciphertext
        header["iv_gov"] = gov_iv
        
        # Increment message counter
        conn["message_n"] += 1
        
        # Encrypt the plaintext message with header as authenticated data
        ciphertext = encrypt_with_gcm(aes_sending_key, plaintext, receiver_iv, str(header))
        
        return header, ciphertext

    def receive_message(self, name: str, message: tuple[dict, tuple[bytes, bytes]]) -> str:
        """
        Decrypt a message received from another user.
        Inputs:
            name: str
            message: tuple(dict, tuple(bytes, bytes))
        Returns:
            plaintext: str
        """
        header, ciphertext = message
        
        # Get sender's certificate
        sender_cert = self.certs.get(name)
        if not sender_cert:
            raise ValueError(f"No certificate found for user {name}")
        
        # Initialize connection if it doesn't exist
        if name not in self.conns:
            self._initialize_receiving_session(name, header)
        
        conn = self.conns[name]
        
        # Check if we need to perform a DH ratchet
        sender_dh_public_key = header["dh_public_key"]
        if sender_dh_public_key != conn.get("their_dh_public_key", None):
            self._ratchet_dh_receiving_keys(name, header)
        
        # Skip messages we've already seen
        if header["message_n"] < conn.get("their_message_n", 0):
            raise ValueError("Message replay detected!")
        
        # Get the expected message number
        expected_message_n = conn.get("their_message_n", 0)
        
        # Check if this is the expected next message
        if header["message_n"] == expected_message_n:
            # Get the next key
            receiving_key, conn["receiving_chain_key"] = self._ratchet_receiving_chain(conn["receiving_chain_key"])
            
            # Convert to AES key
            aes_receiving_key = hmac_to_aes_key(receiving_key, "decrypt")
            
            # Decrypt
            try:
                plaintext = decrypt_with_gcm(aes_receiving_key, ciphertext, header["receiver_iv"], str(header))
                
                # Update message counter
                conn["their_message_n"] = header["message_n"] + 1
                
                # Set flag for DH ratchet on next send if we received their message
                conn["need_ratchet"] = True
                
                return plaintext
            except Exception as e:
                raise ValueError("Message tampering detected!")
        else:
            # This isn't the expected message - could be out of order
            raise ValueError("Message tampering detected!")

    def _initialize_sending_session(self, recipient_name: str) -> None:
        """
        Initialize a new sending session with another user.
        """
        # Get recipient's certificate
        recipient_cert = self.certs[recipient_name]
        
        # Create new DH key pair for this session
        dh_keys = generate_eg()
        
        # Compute the shared secret (root key)
        shared_secret = compute_dh(self.my_keys["private"], recipient_cert["public_key"])
        
        # Initialize connection state
        self.conns[recipient_name] = {
            "my_dh_private_key": dh_keys["private"],
            "my_dh_public_key": dh_keys["public"],
            "their_dh_public_key": None,  # Will be updated when we receive a message
            "root_key": shared_secret,
            "sending_chain_key": None,
            "receiving_chain_key": None,
            "message_n": 0,
            "their_message_n": -1,
            "prev_chain_length": 0,
            "need_ratchet": False
        }
        
        # Initialize sending chain
        salt = gen_random_salt()
        chain_key, next_key = hkdf(shared_secret, salt, "sending_chain_init")
        self.conns[recipient_name]["sending_chain_key"] = chain_key

    def _initialize_receiving_session(self, sender_name: str, header: dict) -> None:
        """
        Initialize a new receiving session with another user.
        """
        # Get sender's certificate
        sender_cert = self.certs[sender_name]
        
        # Compute the shared secret (root key)
        shared_secret = compute_dh(self.my_keys["private"], sender_cert["public_key"])
        
        # Initialize connection state
        self.conns[sender_name] = {
            "my_dh_private_key": self.my_keys["private"],
            "my_dh_public_key": self.my_keys["public"],
            "their_dh_public_key": header["dh_public_key"],
            "root_key": shared_secret,
            "sending_chain_key": None,
            "receiving_chain_key": None,
            "message_n": 0,
            "their_message_n": -1,
            "prev_chain_length": 0,
            "need_ratchet": False
        }
        
        # Initialize receiving chain
        salt = gen_random_salt()
        next_key, chain_key = hkdf(shared_secret, salt, "receiving_chain_init")
        self.conns[sender_name]["receiving_chain_key"] = chain_key

    def _ratchet_dh_sending_keys(self, recipient_name: str) -> None:
        """
        Perform a DH ratchet for sending keys.
        """
        conn = self.conns[recipient_name]
        
        # Store previous chain length for the receiver
        conn["prev_chain_length"] = conn["message_n"]
        
        # Reset message counter
        conn["message_n"] = 0
        
        # Generate new DH key pair
        dh_keys = generate_eg()
        conn["my_dh_private_key"] = dh_keys["private"]
        conn["my_dh_public_key"] = dh_keys["public"]
        
        # Compute new shared secret
        dh_output = compute_dh(conn["my_dh_private_key"], conn["their_dh_public_key"])
        
        # Derive new root key and chain keys
        salt = gen_random_salt()
        conn["root_key"], conn["sending_chain_key"] = hkdf(dh_output, salt, "dh_ratchet_sending")
        
        # Reset ratchet flag
        conn["need_ratchet"] = False

    def _ratchet_dh_receiving_keys(self, sender_name: str, header: dict) -> None:
        """
        Perform a DH ratchet for receiving keys.
        """
        conn = self.conns[sender_name]
        
        # Update their DH public key
        conn["their_dh_public_key"] = header["dh_public_key"]
        
        # Compute new shared secret
        dh_output = compute_dh(conn["my_dh_private_key"], conn["their_dh_public_key"])
        
        # Derive new root key and chain keys
        salt = gen_random_salt()
        conn["root_key"], conn["receiving_chain_key"] = hkdf(dh_output, salt, "dh_ratchet_receiving")

    def _ratchet_sending_chain(self, current_key: bytes) -> tuple[bytes, bytes]:
        """
        Ratchet the sending chain to get the next message key.
        Returns (message_key, next_chain_key)
        """
        message_key = hmac_to_hmac_key(current_key, "message_key")
        next_chain_key = hmac_to_hmac_key(current_key, "next_chain_key")
        return message_key, next_chain_key

    def _ratchet_receiving_chain(self, current_key: bytes) -> tuple[bytes, bytes]:
        """
        Ratchet the receiving chain to get the next message key.
        Returns (message_key, next_chain_key)
        """
        message_key = hmac_to_hmac_key(current_key, "message_key")
        next_chain_key = hmac_to_hmac_key(current_key, "next_chain_key")
        return message_key, next_chain_key