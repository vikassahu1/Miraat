from cryptography.fernet import Fernet
key = Fernet.generate_key()
print("Your new encryption key is:")
print(key.decode())