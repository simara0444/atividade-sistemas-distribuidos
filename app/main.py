from fastapi import FastAPI, HTTPException, Header
from app.db import connect_db, close_db
from app import crud, auth_utils, schemas
from datetime import datetime, timedelta, timezone
from app.redis_client import redis_client, connect_redis
import uvicorn

MAX_ATTEMPTS = 3
BLOCK_MINUTES = 10
ME_RATE_LIMIT = 5
ME_RATE_EXPIRE = 60  

app = FastAPI(title="Microsserviço de Autenticação - SDWork")


@app.on_event("startup")
async def startup():
    print(">>> startup: conectando ao DB")
    await connect_db()
    print(">>> DB conectado")
    
    print(">>> conectando ao Redis")
    await connect_redis()
    print(">>> Redis conectado")


@app.on_event("shutdown")
async def shutdown():
    print(">>> shutdown: fechando conexão DB")
    await close_db()


@app.post("/api/v1/auth/signup", response_model=schemas.UserResponse)
async def signup(payload: schemas.SignupRequest):
    if await crud.buscar_usuario_por_email(payload.email):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    if await crud.buscar_usuario_por_documento(payload.documento):
        raise HTTPException(status_code=400, detail="Documento já cadastrado")

    user = await crud.criar_usuario(payload.email, payload.documento, payload.senha, payload.nome)
    token = auth_utils.make_token(user["email"], user["documento"])
    await crud.inserir_token(token, user["id"])

    user = dict(user)
    user["token"] = token
    print(f"[signup] criado user id={user['id']} email={user['email']}")
    return user


@app.post("/api/v1/auth/login", response_model=schemas.TokenResponse)
async def login(payload: schemas.LoginRequest):
    user = await crud.buscar_usuario_por_email(payload.login)
    attempt = await crud.buscar_login_attempt(payload.login)
    now = datetime.now(timezone.utc)

    if attempt:
        last = attempt.get("last_attempt") or now
        if isinstance(last, str):
            try:
                last = datetime.fromisoformat(last.replace("Z", "+00:00"))
            except Exception:
                last = now
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        diff = now - last
        if attempt.get("tentativa_count", 0) >= MAX_ATTEMPTS:
            if diff < timedelta(minutes=BLOCK_MINUTES):
                raise HTTPException(
                    status_code=403,
                    detail=f"Usuário bloqueado por {BLOCK_MINUTES} minutos devido a tentativas falhas"
                )
            else:
                await crud.criar_ou_atualizar_login_attempt(payload.login, sucesso=True)

    if not user or user["senha"] != payload.senha:
        await crud.criar_ou_atualizar_login_attempt(payload.login, sucesso=False)
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    await crud.criar_ou_atualizar_login_attempt(payload.login, sucesso=True)
    token = auth_utils.make_token(user["email"], user["documento"])
    await crud.inserir_token(token, user["id"])
    return {"token": token}


@app.post("/api/v1/auth/recuperar-senha", response_model=schemas.TokenResponse)
async def recuperar_senha(payload: schemas.RecuperarSenhaRequest):
    user = await crud.buscar_usuario_por_email_e_documento(payload.email, payload.documento)
    if not user:
        raise HTTPException(status_code=404, detail="Email e documento não correspondem")

    updated = await crud.atualizar_senha(user["id"], payload.nova_senha)
    new_token = auth_utils.make_token(updated["email"], updated["documento"])
    await crud.deletar_tokens_do_usuario(user["id"])
    await crud.inserir_token(new_token, user["id"])
    return {"token": new_token}


@app.post("/api/v1/auth/logout")
async def logout(authorization: str | None = Header(None)):
    token = auth_utils.get_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=400, detail="Token ausente")
    if not await crud.buscar_token(token):
        raise HTTPException(status_code=400, detail="Token inválido")
    await crud.deletar_token(token)
    return {"detail": "Logout realizado com sucesso"}


async def check_me_throttle(token: str):
    """Checa se o usuário excedeu o limite /me"""
    if not redis_client:
        return  # Redis não disponível, apenas permite
    key = f"me:{token}"
    count = await redis_client.get(key)
    count = int(count) if count else 0
    if count >= ME_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Muitas requisições em /me, tente mais tarde")
    await redis_client.incr(key)
    await redis_client.expire(key, ME_RATE_EXPIRE)


@app.get("/api/v1/auth/me", response_model=schemas.UserResponse)
async def me(authorization: str | None = Header(None)):
    token = auth_utils.get_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=400, detail="Token ausente")

    await check_me_throttle(token)

    token_row = await crud.buscar_token(token)
    if not token_row:
        raise HTTPException(status_code=400, detail="Token inválido")
    user = await crud.buscar_usuario_por_id(token_row["id"])
    user = dict(user)
    user["token"] = token
    return user


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
