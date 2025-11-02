from cryptography.fernet import Fernet
import os

SECRET_KEY = os.getenv("SECRET_KEY", "SUA_CHAVE_AQUI_COM_32BYTES==")
fernet = Fernet(SECRET_KEY.encode())

def make_token(email: str, documento: str) -> str:
    raw = f"{email}:{documento}"
    token_bytes = fernet.encrypt(raw.encode())
    return token_bytes.decode()

def parse_token(token: str):
    try:
        decoded_bytes = fernet.decrypt(token.encode())
        decoded = decoded_bytes.decode()
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
