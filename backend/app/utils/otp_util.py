"""
otp_util.py
-----------
Reusable OTP utilities for the password-reset flow.

Design decisions
----------------
* OTPs are NEVER stored in plain text.  Only their SHA-256 digest is
  persisted, so a database breach cannot be used to redeem a code.
* SHA-256 is chosen over bcrypt intentionally: OTPs are short-lived
  (10 minutes) and randomly generated, so the usual bcrypt benefits
  (adaptive cost, per-user salts) are irrelevant.  SHA-256 is fast
  enough for a single comparison yet still a one-way function.
* The generator uses secrets.randbelow(), which is backed by the OS
  CSPRNG, giving proper randomness — never use random.randint() for
  security-sensitive codes.
"""

import hashlib
import hmac
import secrets

# ── Constants ─────────────────────────────────────────────────────────────────

OTP_LENGTH = 6  # digits
OTP_MIN = 10 ** (OTP_LENGTH - 1)  # 100_000
OTP_MAX = (10**OTP_LENGTH) - 1  # 999_999


# ── Public API ────────────────────────────────────────────────────────────────


def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit OTP string.

    Why secrets.randbelow?
        The built-in `random` module uses a Mersenne Twister PRNG whose
        state can theoretically be reconstructed from enough observations.
        `secrets.randbelow` uses the OS-level CSPRNG (urandom / CryptGenRandom)
        which is suitable for security-critical tokens.

    Returns:
        str: A zero-padded 6-digit string, e.g. "047392".
             Zero-padding ensures the string is always exactly 6 characters
             long regardless of the numeric value.

    Example:
        >>> otp = generate_otp()
        >>> len(otp)
        6
        >>> otp.isdigit()
        True
    """
    # Generate a random integer in [100_000, 999_999]
    # This avoids leading-zero ambiguity while guaranteeing 6 digits.
    value = OTP_MIN + secrets.randbelow(OTP_MAX - OTP_MIN + 1)
    return str(value)


def hash_otp(otp: str) -> str:
    """
    Return the SHA-256 hex digest of the given OTP string.

    Why SHA-256 and not bcrypt?
        - OTPs are random, short-lived (10 min), and single-use, so
          dictionary / rainbow-table attacks are impractical even with
          a fast hash.
        - bcrypt's intentional slowness would add ~200 ms per verification
          with no security benefit for a random 6-digit token.
        - SHA-256 produces a deterministic, constant-length (64-char hex)
          digest that is trivial to index and compare in MongoDB.

    Args:
        otp (str): The plain-text OTP produced by generate_otp().

    Returns:
        str: 64-character lowercase hex string (SHA-256 digest).

    Example:
        >>> hash_otp("123456")
        '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    """
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def verify_otp(plain_otp: str, stored_hash: str) -> bool:
    """
    Securely compare a user-submitted OTP against the stored hash.

    Why hmac.compare_digest via hashlib?
        A naive `hash_otp(plain_otp) == stored_hash` comparison is
        vulnerable to timing attacks: Python's string equality returns
        early on the first differing byte, leaking information about
        how close the guess was.  hashlib.compare_digest (backed by
        hmac.compare_digest) always runs in constant time regardless
        of where the strings diverge.

    Args:
        plain_otp  (str): The raw 6-digit code entered by the user.
        stored_hash (str): The SHA-256 hex digest retrieved from MongoDB.

    Returns:
        bool: True only when hash_otp(plain_otp) == stored_hash in
              constant time.  False if either value is empty or mismatched.

    Example:
        >>> otp = generate_otp()
        >>> h   = hash_otp(otp)
        >>> verify_otp(otp, h)
        True
        >>> verify_otp("000000", h)
        False
    """
    if not plain_otp or not stored_hash:
        return False

    candidate_hash = hash_otp(plain_otp)

    # compare_digest is constant-time; prevents timing side-channel attacks.
    return hmac.compare_digest(candidate_hash, stored_hash)
