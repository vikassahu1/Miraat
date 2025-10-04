import os
import base64
from cryptography.fernet import Fernet, InvalidToken

class EncryptionService:
    def __init__(self):
        """
        Initializes the encryption service by loading the key from environment variables.
        """
        raw_key = os.environ.get("ENCRYPTION_KEY")
        if not raw_key:
            raise ValueError("ENCRYPTION_KEY not found in environment variables. Cannot start application.")
        
        # Clean and validate the key
        key = raw_key.strip().strip('"').strip("'")
        
        # Validate key format
        try:
            decoded = base64.urlsafe_b64decode(key)
            if len(decoded) != 32:
                raise ValueError("Key must decode to 32 bytes")
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")
        
        self.fernet = Fernet(key)
        print("EncryptionService initialized successfully.")

    def encrypt_data(self, data: str) -> str:
        """
        Encrypts a string and returns a base64-encoded string for database storage.
        """
        if not isinstance(data, str):
            raise ValueError("Data to be encrypted must be a string.")
        
        # Encrypt and encode to base64 string for database storage
        encrypted_bytes = self.fernet.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_data(self, encrypted_data) -> str:
        """
        Decrypts data from database and returns the original string.
        Handles both string and bytes input from database.
        """
        try:
            # Handle different input types from database
            if isinstance(encrypted_data, str):
                # String from database - decode from base64
                encrypted_bytes = base64.b64decode(encrypted_data)
            elif isinstance(encrypted_data, bytes):
                # Bytes from database - could be raw bytes or base64-encoded bytes
                try:
                    # Try to decode as base64 first
                    encrypted_bytes = base64.b64decode(encrypted_data)
                except:
                    # If that fails, assume it's raw encrypted bytes
                    encrypted_bytes = encrypted_data
            else:
                raise ValueError(f"Unsupported data type for decryption: {type(encrypted_data)}")
            
            # Decrypt the bytes
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")