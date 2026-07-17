import base64
import hashlib
import hmac
import json
import time

from app.core.config import get_settings


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + settings.auth_token_ttl_seconds,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = hmac.new(settings.auth_secret_key.get_secret_value().encode(), encoded, hashlib.sha256).digest()
    return f"{encoded.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def decode_access_token(token: str) -> dict[str, object] | None:
    try:
        encoded_text, signature_text = token.split(".", 1)
        encoded = encoded_text.encode()
        padding = b"=" * (-len(signature_text) % 4)
        signature = base64.urlsafe_b64decode(signature_text.encode() + padding)
        expected = hmac.new(
            get_settings().auth_secret_key.get_secret_value().encode(), encoded, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload_padding = b"=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(encoded + payload_padding))
        if int(payload["exp"]) <= int(time.time()):
            return None
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
