import keyring

SERVICE = "MarkWise"
USERNAME = "gemini_api_key"
_session_key = None  # fallback when no system keyring exists (some minimal Linux setups)


def save_api_key(key: str) -> bool:
    """Returns True if saved in the system keyring, False if kept for this session only."""
    global _session_key
    _session_key = key
    try:
        keyring.set_password(SERVICE, USERNAME, key)
        return True
    except Exception:
        return False


def load_api_key():
    if _session_key:
        return _session_key
    try:
        return keyring.get_password(SERVICE, USERNAME)
    except Exception:
        return None
