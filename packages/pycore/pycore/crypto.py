from cryptography.fernet import Fernet

_PREFIX = "enc:"


def fernet_encrypt(value: str, key: str) -> str:
    """Encrypt value with Fernet key. Returns enc:<ciphertext>."""
    f = Fernet(key.encode())
    return f"{_PREFIX}{f.encrypt(value.encode()).decode()}"


def fernet_decrypt(value: str, key: str) -> str:
    """Decrypt enc:<ciphertext>. Returns plaintext (passthrough if not encrypted)."""
    if not value.startswith(_PREFIX):
        return value
    f = Fernet(key.encode())
    return f.decrypt(value[len(_PREFIX) :].encode()).decode()


def generate_key() -> str:
    """Generates a new Fernet key."""
    return Fernet.generate_key().decode()
