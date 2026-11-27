"""Base62 conversion helpers."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode_base62(value: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return "0"

    encoded = []
    while value:
        value, remainder = divmod(value, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode_base62(encoded: str) -> int:
    """Decode a base62 string into a non-negative integer."""
    if not isinstance(encoded, str):
        raise TypeError("encoded value must be a string")
    if not encoded:
        raise ValueError("encoded value must not be empty")

    value = 0
    for character in encoded:
        try:
            digit = ALPHABET.index(character)
        except ValueError as exc:
            raise ValueError(f"invalid base62 character: {character!r}") from exc
        value = value * BASE + digit
    return value
