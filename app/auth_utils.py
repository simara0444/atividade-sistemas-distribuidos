import base64

def make_token(email: str, documento: str) -> str:
    raw = f"{email}:{documento}"
    return base64.b64encode(raw.encode()).decode()

def parse_token(token: str):
    try:
        decoded = base64.b64decode(token.encode()).decode()
        if ":" in decoded:
            email, documento = decoded.split(":", 1)
            return email, documento
    except Exception:
        return None
    return None

def get_token_from_header(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts
    if scheme != "SDWork":
        return None
    return token
