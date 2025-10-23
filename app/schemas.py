from pydantic import BaseModel, EmailStr

# Signup
class SignupRequest(BaseModel):
    email: EmailStr
    documento: str
    senha: str
    nome: str | None = None

# Login
class LoginRequest(BaseModel):
    login: EmailStr
    senha: str

# Recuperar senha
class RecuperarSenhaRequest(BaseModel):
    email: EmailStr
    documento: str
    nova_senha: str

# Token response
class TokenResponse(BaseModel):
    token: str

# Usuário response
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    documento: str
    senha: str
    nome: str | None
    token: str
