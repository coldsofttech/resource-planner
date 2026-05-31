import hashlib
import secrets


def generate_otp(digits: int = 6) -> tuple[str, str]:
    """Generate a numeric OTP. Returns (code, code_hash)."""
    code = f"{secrets.randbelow(10 ** digits):0{digits}d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    return code, code_hash


def hash_otp(code: str) -> str:
    """Return the SHA-256 hex digest for a given OTP code."""
    return hashlib.sha256(code.encode()).hexdigest()
