"""
legacy_demo.py — Test fixture for static crypto scanner validation.

⚠️ WARNING: This file intentionally uses weak/legacy cryptographic primitives
   for the sole purpose of testing the CryptoScan static analysis engine.
   All keys and data are DUMMY values. Do NOT use any of this in production.
"""

import hashlib
import random

# --- Dummy placeholder (NOT a real key) ---
DEMO_API_KEY = "DUMMY-NOT-A-REAL-KEY-0000"


def legacy_password_hash(pw: str) -> str:
    """MD5 password hash — intentionally weak for scanner testing."""
    return hashlib.md5(pw.encode()).hexdigest()        # weak hash


def legacy_checksum(data: bytes) -> str:
    """SHA-1 checksum — intentionally weak for scanner testing."""
    return hashlib.sha1(data).hexdigest()              # weak hash


def weak_token() -> str:
    """Non-cryptographic RNG token — intentionally weak for scanner testing."""
    return str(random.random())                        # non-crypto RNG
