from app.db import fetchrow, fetch, execute
from typing import Optional
from datetime import datetime, timezone


async def criar_usuario(email: str, documento: str, senha: str, nome: Optional[str]):
    query = """
    INSERT INTO usuarios (email, documento, senha, nome)
    VALUES ($1, $2, $3, $4)
    RETURNING id, email, documento, senha, nome, token
    """
    return await fetchrow(query, email, documento, senha, nome)

async def buscar_usuario_por_email(email: str):
    query = "SELECT * FROM usuarios WHERE email = $1"
    return await fetchrow(query, email)

async def buscar_usuario_por_documento(documento: str):
    query = "SELECT * FROM usuarios WHERE documento = $1"
    return await fetchrow(query, documento)

async def buscar_usuario_por_email_e_documento(email: str, documento: str):
    query = "SELECT * FROM usuarios WHERE email = $1 AND documento = $2"
    return await fetchrow(query, email, documento)

async def buscar_usuario_por_id(usuario_id: int):
    query = "SELECT * FROM usuarios WHERE id = $1"
    return await fetchrow(query, usuario_id)

async def atualizar_senha(usuario_id: int, nova_senha: str):
    query = """
    UPDATE usuarios 
    SET senha = $1 
    WHERE id = $2 
    RETURNING id, email, documento, senha, nome, token
    """
    return await fetchrow(query, nova_senha, usuario_id)


async def inserir_token(token: str, usuario_id: int):
    query = "UPDATE usuarios SET token = $1 WHERE id = $2"
    return await execute(query, token, usuario_id)

async def buscar_token(token: str):
    query = "SELECT * FROM usuarios WHERE token = $1"
    return await fetchrow(query, token)

async def deletar_token(token: str):
    query = "UPDATE usuarios SET token = NULL WHERE token = $1"
    return await execute(query, token)

async def deletar_tokens_do_usuario(usuario_id: int):
    query = "UPDATE usuarios SET token = NULL WHERE id = $1"
    return await execute(query, usuario_id)


async def buscar_login_attempt(email: str):
    query = "SELECT * FROM login_attempts WHERE email = $1"
    return await fetchrow(query, email)

async def criar_ou_atualizar_login_attempt(email: str, sucesso: bool):
    """
    Insere se não existir. Se existir:
     - sucesso=True => zera contador e atualiza last_attempt
     - sucesso=False => incrementa contador e atualiza last_attempt
    Sempre grava last_attempt como UTC-aware.
    """
    attempt = await buscar_login_attempt(email)
    now = datetime.now(timezone.utc)

    print(f"[crud] criar_ou_atualizar_login_attempt email={email} sucesso={sucesso} now={now.isoformat()} attempt={attempt}")

    if not attempt:
        count = 0 if sucesso else 1
        query = "INSERT INTO login_attempts (email, tentativa_count, last_attempt) VALUES ($1, $2, $3)"
        await execute(query, email, count, now)
        print(f"[crud] inserido login_attempt email={email} count={count}")
        return


    current = attempt.get("tentativa_count") or 0

    if sucesso:
        query = "UPDATE login_attempts SET tentativa_count = 0, last_attempt = $2 WHERE email = $1"
        await execute(query, email, now)
        print(f"[crud] zera contador para email={email}")
    else:
        new_count = current + 1
        query = "UPDATE login_attempts SET tentativa_count = $2, last_attempt = $3 WHERE email = $1"
        await execute(query, email, new_count, now)
        print(f"[crud] incrementa contador para email={email} new_count={new_count}")
