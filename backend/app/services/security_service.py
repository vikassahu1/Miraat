# Miraat/backend/app/services/security_service.py
import os
from cryptography.fernet import Fernet, InvalidToken

class EncryptionService:
    def __init__(self):
        """
        Initializes the encryption service by loading the key from environment variables.
        """
        key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY not found in environment variables. Cannot start application.")
        
        self.key = key.encode() # Fernet key must be bytes
        self.fernet = Fernet(self.key)
        print("EncryptionService initialized successfully.")

    def encrypt_data(self, data: str) -> str:
        """
        Encrypts a string and returns it as a URL-safe, encoded string.
        """
        if not isinstance(data, str):
            raise TypeError("Data to be encrypted must be a string.")
            
        encrypted_data = self.fernet.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypts an encoded string and returns the original string.
        Returns an error message if decryption fails.
        """
        if not isinstance(encrypted_data, str):
            raise TypeError("Data to be decrypted must be a string.")

        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except InvalidToken:
            # This happens if the key is wrong or the data is corrupted
            return "[DECRYPTION FAILED: Invalid Token]"
        except Exception as e:
            return f"[DECRYPTION FAILED: {str(e)}]"