from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    documento: str
    senha: str
    nome: str | None = None


class LoginRequest(BaseModel):
    login: EmailStr
    senha: str


class RecuperarSenhaRequest(BaseModel):
    email: EmailStr
    documento: str
    nova_senha: str


class TokenResponse(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    documento: str
    senha: str
    nome: str | None
    token: str
