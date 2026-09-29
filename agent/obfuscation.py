import base64
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
]

def encode_payload(raw_text: str) -> str:
    """Encodes plaintext string output into safe Base64 string."""
    if not raw_text:
        return ""
    return base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')

def decode_payload(encoded_text: str) -> str:
    """Decodes incoming Base64 task commands into plain text."""
    if not encoded_text:
        return ""
    try:
        return base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
    except Exception:
        return encoded_text

def get_stealth_headers() -> dict:
    """Generates realistic HTTP headers mimicking standard web browser traffic."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US, en; q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

if __name__ == "__main__":
    print("[*] Testing payload obfuscation...")
    original = "whoami /priv"
    encoded = encode_payload(original)
    decoded = decode_payload(encoded)
    headers = get_stealth_headers()
    
    print(f"Original: {original}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Sample Headers: {headers}")
    
    assert original == decoded, "Encoding roundtrip failed!"
    print("[+] All obfuscation tests passed successfully!")