import hashlib


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
