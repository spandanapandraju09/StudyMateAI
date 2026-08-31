# backend/utils/otp.py
"""Utility functions for generating and verifying OTP codes.

The OTP is a 6‑digit numeric string generated using the `secrets` module for cryptographic
security. OTPs are hashed with bcrypt before being stored in the database.
"""
import secrets
import bcrypt
from datetime import datetime, timedelta

# Configuration constants (can be overridden via environment if needed)
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5

def generate_otp() -> str:
    """Generate a secure random 6‑digit OTP as a string."""
    return str(secrets.randbelow(10 ** OTP_LENGTH)).zfill(OTP_LENGTH)

def hash_otp(otp: str) -> str:
    """Hash the OTP using bcrypt and return the decoded string.

    The returned value can be stored directly in a TEXT column.
    """
    hashed = bcrypt.hashpw(otp.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_otp(otp: str, hashed: str) -> bool:
    """Verify a plain OTP against its bcrypt hash.

    Returns ``True`` if the OTP matches, ``False`` otherwise.
    """
    try:
        return bcrypt.checkpw(otp.encode(), hashed.encode())
    except Exception:
        return False

def otp_expiration_time() -> datetime:
    """Return the datetime at which a newly‑generated OTP should expire."""
    return datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
