from fastapi import FastAPI, HTTPException, Header
from auth import login, register
from session import create_session_token, validate_token

app = FastAPI()

@app.post("/auth/login")
def api_login(body: dict):
    result = login(body["username"], body["password"])
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    token = create_session_token(result["user_id"], result["role"])
    return {"token": token}

@app.post("/auth/register")
def api_register(body: dict):
    result = register(body["username"], body["password"])
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Account created successfully"}


