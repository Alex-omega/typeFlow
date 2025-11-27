import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Optional

from . import config

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError as exc:  # pragma: no cover - dependency might be missing locally
    raise RuntimeError(
        "cryptography is required for encryption. Install via `pip install cryptography`."
    ) from exc


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=config.KEY_LENGTH,
        salt=salt,
        iterations=config.KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


@dataclass
class PasswordRecord:
    salt_b64: str
    verifier_b64: str

    @property
    def salt(self) -> bytes:
        return base64.b64decode(self.salt_b64)

    @property
    def verifier(self) -> bytes:
        return base64.b64decode(self.verifier_b64)


class CryptoManager:
    def __init__(self, password: str, salt: Optional[bytes] = None):
        self.salt = salt or os.urandom(config.SALT_BYTES)
        self.key = _derive_key(password, self.salt)
        self.password = password  # keep in-memory for service reuse

    def password_record(self) -> PasswordRecord:
        verifier = hmac.new(self.key, b"typeflow-password", hashlib.sha256).digest()
        return PasswordRecord(
            salt_b64=base64.b64encode(self.salt).decode("ascii"),
            verifier_b64=base64.b64encode(verifier).decode("ascii"),
        )

    @staticmethod
    def verify_password(password: str, record: PasswordRecord) -> Optional["CryptoManager"]:
        salt = record.salt
        key = _derive_key(password, salt)
        expected = hmac.new(key, b"typeflow-password", hashlib.sha256).digest()
        if not hmac.compare_digest(expected, record.verifier):
            return None
        mgr = CryptoManager(password, salt=salt)
        mgr.key = key
        return mgr

    def encrypt_text(self, text: str) -> str:
        aes = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aes.encrypt(nonce, text.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt_text(self, blob_b64: str) -> str:
        data = base64.b64decode(blob_b64)
        nonce, ciphertext = data[:12], data[12:]
        aes = AESGCM(self.key)
        plaintext = aes.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
