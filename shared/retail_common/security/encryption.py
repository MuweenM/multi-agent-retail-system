from cryptography.fernet import Fernet
from shared.retail_common.config import settings

def get_cipher() -> Fernet:
    return Fernet(settings.encryption_key.encode())

def encrypt_text(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    cipher = get_cipher()
    return cipher.encrypt(plain_text.encode()).decode()

def decrypt_text(encrypted_text: str) -> str:
    if not encrypted_text:
        return encrypted_text
    cipher = get_cipher()
    return cipher.decrypt(encrypted_text.encode()).decode()
