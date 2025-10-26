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
        Handles string, bytes, memoryview, and any other database return types.
        """
        try:
            # Convert input to bytes for processing
            if isinstance(encrypted_data, str):
                # String from database - this is what we expect
                encrypted_data_bytes = encrypted_data.encode('utf-8')
            elif isinstance(encrypted_data, bytes):
                # Already bytes
                encrypted_data_bytes = encrypted_data
            elif isinstance(encrypted_data, memoryview):
                # PostgreSQL sometimes returns memoryview
                encrypted_data_bytes = bytes(encrypted_data)
            else:
                # Try to convert whatever it is to bytes
                encrypted_data_bytes = str(encrypted_data).encode('utf-8')
            
            # Decode from base64 to get the actual encrypted bytes
            try:
                actual_encrypted_bytes = base64.b64decode(encrypted_data_bytes)
            except Exception as decode_error:
                raise ValueError(f"Failed to decode base64: {decode_error}")
            
            # Decrypt using Fernet
            try:
                decrypted_bytes = self.fernet.decrypt(actual_encrypted_bytes)
            except Exception as decrypt_error:
                raise ValueError(f"Fernet decryption failed: {decrypt_error}")
            
            # Return as UTF-8 string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            # Detailed error for debugging
            raise ValueError(f"Decryption failed: {str(e)}. Input type: {type(encrypted_data)}, Input length: {len(encrypted_data) if hasattr(encrypted_data, '__len__') else 'unknown'}")