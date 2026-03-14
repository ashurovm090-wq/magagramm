from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

# База данных
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
async def startup():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)')
    conn.commit()
    conn.close()

active_connections = {}

@app.get("/")
async def get_index(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/login")
async def get_login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...), fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', (username.lower(), fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

@app.websocket("/ws/{username}")
async def ws_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Формат: "кому:сообщение"
            if ":" in data:
                to_user, msg = data.split(":", 1)
                if to_user in active_connections:
                    await active_connections[to_user].send_text(f"{username}: {msg}")
                # Отправителю тоже шлем, чтобы он видел своё сообщение
                await websocket.send_text(f"{username}: {msg}")
    except WebSocketDisconnect:
        del active_connections[username]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
