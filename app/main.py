from fastapi import FastAPI, HTTPException, Header
from app.db import connect_db, close_db
from app import crud, auth_utils, schemas
from datetime import datetime, timedelta, timezone
import uvicorn

MAX_ATTEMPTS = 3
BLOCK_MINUTES = 10

app = FastAPI(title="Microsserviço de Autenticação - SDWork")


@app.on_event("startup")
async def startup():
    print(">>> startup: conectando ao DB")
    await connect_db()
    print(">>> startup: conectado")


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
    print(f"[login] tentativa para login={payload.login}")
    user = await crud.buscar_usuario_por_email(payload.login)
    attempt = await crud.buscar_login_attempt(payload.login)
    now = datetime.now(timezone.utc)

    print(f"[login] now={now.isoformat()}")
    print(f"[login] user found? {'yes' if user else 'no'}")
    print(f"[login] attempt row={attempt}")

   
    if attempt:
        last = attempt.get("last_attempt")
        print(f"[login] raw last_attempt={last!r} (type {type(last)})")

        if isinstance(last, str):
            try:
                last = datetime.fromisoformat(last.replace("Z", "+00:00"))
                print(f"[login] parsed last_attempt as {last.isoformat()}")
            except Exception as e:
                print(f"[login] ERRO ao parse last_attempt string: {e}; setando last = now")
                last = now

       
        if last is None:
            print("[login] last_attempt is None -> setando last = now")
            last = now

       
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
            print(f"[login] last_attempt tzinfo ajustado -> {last.isoformat()}")

        diff = now - last
        minutos_passados = diff.total_seconds() / 60.0
        print(f"[login] tentativa_count={attempt.get('tentativa_count')} last={last.isoformat()} diff_minutes={minutos_passados:.2f}")

        if attempt.get("tentativa_count", 0) >= MAX_ATTEMPTS:
            if diff < timedelta(minutes=BLOCK_MINUTES):
                print(f"[login] BLOQUEADO: faltam {(BLOCK_MINUTES - minutos_passados):.2f} minutos")
                raise HTTPException(
                    status_code=403,
                    detail=f"Usuário bloqueado por {BLOCK_MINUTES} minutos devido a tentativas falhas"
                )
            else:
        
                print("[login] bloqueio expirou -> zerando contador no DB")
                await crud.criar_ou_atualizar_login_attempt(payload.login, sucesso=True)


    if not user or user["senha"] != payload.senha:
        print("[login] credenciais inválidas -> incrementando tentativa")
        await crud.criar_ou_atualizar_login_attempt(payload.login, sucesso=False)
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

  
    print("[login] credenciais corretas -> resetando tentativa e gerando token")
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


@app.get("/api/v1/auth/me", response_model=schemas.UserResponse)
async def me(authorization: str | None = Header(None)):
    token = auth_utils.get_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=400, detail="Token ausente")
    token_row = await crud.buscar_token(token)
    if not token_row:
        raise HTTPException(status_code=400, detail="Token inválido")
    user = await crud.buscar_usuario_por_id(token_row["id"])
    user = dict(user)
    user["token"] = token
    return user


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
