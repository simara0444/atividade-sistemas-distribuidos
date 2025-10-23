from app.db import fetchrow, execute
from typing import Optional

# Criar usuário
async def criar_usuario(email: str, documento: str, senha: str, nome: Optional[str]):
    query = """
    INSERT INTO usuarios (email, documento, senha, nome)
    VALUES ($1, $2, $3, $4)
    RETURNING id, email, documento, senha, nome, token
    """
    return await fetchrow(query, email, documento, senha, nome)

# Buscar usuário por email
async def buscar_usuario_por_email(email: str):
    query = "SELECT * FROM usuarios WHERE email = $1"
    return await fetchrow(query, email)

# Buscar usuário por documento
async def buscar_usuario_por_documento(documento: str):
    query = "SELECT * FROM usuarios WHERE documento = $1"
    return await fetchrow(query, documento)

# Buscar usuário por email e documento
async def buscar_usuario_por_email_e_documento(email: str, documento: str):
    query = "SELECT * FROM usuarios WHERE email = $1 AND documento = $2"
    return await fetchrow(query, email, documento)

# Buscar usuário por ID
async def buscar_usuario_por_id(usuario_id: int):
    query = "SELECT * FROM usuarios WHERE id = $1"
    return await fetchrow(query, usuario_id)

# Atualizar senha
async def atualizar_senha(usuario_id: int, nova_senha: str):
    query = """
    UPDATE usuarios 
    SET senha = $1 
    WHERE id = $2 
    RETURNING id, email, documento, senha, nome, token
    """
    return await fetchrow(query, nova_senha, usuario_id)

# Inserir token
async def inserir_token(token: str, usuario_id: int):
    query = "UPDATE usuarios SET token = $1 WHERE id = $2"
    return await execute(query, token, usuario_id)

# Buscar token
async def buscar_token(token: str):
    query = "SELECT * FROM usuarios WHERE token = $1"
    return await fetchrow(query, token)

# Deletar token
async def deletar_token(token: str):
    query = "UPDATE usuarios SET token = NULL WHERE token = $1"
    return await execute(query, token)

# Deletar tokens de um usuário
async def deletar_tokens_do_usuario(usuario_id: int):
    query = "UPDATE usuarios SET token = NULL WHERE id = $1"
    return await execute(query, usuario_id)
