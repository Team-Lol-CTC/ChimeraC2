import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.obfuscation import (
    encode_payload,
    decode_payload,
    get_stealth_headers,
)


def test_encode_decode():
    original = "Hello ChimeraC2"

    encoded = encode_payload(original)
    decoded = decode_payload(encoded)

    assert encoded != original
    assert decoded == original


def test_empty_payload():
    assert encode_payload("") == ""
    assert decode_payload("") == ""


def test_headers():
    headers = get_stealth_headers()

    assert "User-Agent" in headers
    assert "Accept" in headers
    assert "Content-Type" in headers


def test_unicode_payload():
    original = "ChimeraC2 ሳይበር ላብ"

    encoded = encode_payload(original)
    decoded = decode_payload(encoded)

    assert decoded == original