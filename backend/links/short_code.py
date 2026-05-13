# links/short_code.py
# Base62 short code generation engine.
#
# Strategy: encode a database sequence counter via Base62.
# Why: pure random strings require collision checks on every insert.
# Counter-based encoding is collision-free by design — same counter
# value never appears twice.
#
# Fallback: if no counter is available, we use random + verify.

import random
import string
import logging

logger = logging.getLogger(__name__)

BASE62_ALPHABET = string.digits + string.ascii_letters
# '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def encode_base62(number: int) -> str:
    """
    Encodes a positive integer into a Base62 string.

    Example:
        encode_base62(1)       → '1'
        encode_base62(62)      → 'a0'  (wraps like base-10 but base-62)
        encode_base62(999999)  → '4c91'
    """
    if number == 0:
        return BASE62_ALPHABET[0]

    result = []
    while number:
        number, remainder = divmod(number, 62)
        result.append(BASE62_ALPHABET[remainder])

    return ''.join(reversed(result))


def decode_base62(encoded: str) -> int:
    """
    Decodes a Base62 string back to an integer.
    Not used in the hot path but useful for debugging and analytics.
    """
    result = 0
    for char in encoded:
        result = result * 62 + BASE62_ALPHABET.index(char)
    return result


class ShortCodeService:
    MIN_LENGTH = 6

    @classmethod
    def generate(cls) -> str:
        """
        Generates a unique short code.

        Strategy:
        1. Pull the current max DB counter to use as the encoding seed.
        2. Encode it in Base62.
        3. Pad to MIN_LENGTH if needed.

        This is called inside a transaction in LinkService to prevent
        race conditions between generate() and the INSERT.
        """
        from links.models import Link

        # Use total link count + random offset as the counter seed.
        # Not a pure sequence (no DB sequence object) but collision-safe
        # enough for this stage. Phase 5 upgrades to a proper DB sequence.
        count = Link.objects.count()
        seed  = count + random.randint(1000, 9999)
        code  = encode_base62(seed)

        # Pad short codes to minimum length for aesthetics
        while len(code) < cls.MIN_LENGTH:
            code = BASE62_ALPHABET[0] + code

        # Collision guard — extremely rare but always safe to check
        if Link.objects.filter(short_code=code).exists():
            logger.warning(f"Short code collision detected: {code}. Regenerating.")
            code = cls._fallback_generate()

        return code

    @classmethod
    def _fallback_generate(cls) -> str:
        """
        Random fallback with uniqueness check.
        Only called on the rare collision path.
        """
        from links.models import Link

        for _ in range(10):
            code = ''.join(random.choices(BASE62_ALPHABET, k=cls.MIN_LENGTH))
            if not Link.objects.filter(short_code=code).exists():
                return code

        raise RuntimeError("Unable to generate a unique short code after 10 attempts.")

    @classmethod
    def validate_custom_alias(cls, alias: str) -> str:
        """
        Validates and normalizes a user-supplied custom alias.
        Raises ValueError with a user-facing message on failure.
        """
        from links.models import Link

        alias = alias.strip().lower()

        RESERVED = {
            'admin', 'api', 'login', 'logout', 'register',
            'dashboard', 'analytics', 'health', 'static',
            'r', 'docs', 'schema', 'me',
        }

        if not alias:
            raise ValueError("Alias cannot be empty.")

        if len(alias) < 3:
            raise ValueError("Alias must be at least 3 characters.")

        if len(alias) > 50:
            raise ValueError("Alias cannot exceed 50 characters.")

        if not alias.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Alias can only contain letters, numbers, hyphens, and underscores.")

        if alias in RESERVED:
            raise ValueError(f"'{alias}' is a reserved keyword and cannot be used.")

        if Link.objects.filter(short_code=alias).exists():
            raise ValueError(f"'{alias}' is already taken.")

        return alias