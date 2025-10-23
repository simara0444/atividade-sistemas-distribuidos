from fastapi import FastAPI, HTTPException, Header
from app.db import connect_db, close_db
from app import crud, auth_utils, schemas
import uvicorn

app = FastAPI(title="Microsserviço de Autenticação - SDWork")

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
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
    return user


@app.post("/api/v1/auth/login", response_model=schemas.TokenResponse)
async def login(payload: schemas.LoginRequest):
    user = await crud.buscar_usuario_por_email(payload.login)
    if not user or user["senha"] != payload.senha:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
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
