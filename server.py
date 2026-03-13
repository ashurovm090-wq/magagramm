from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, bio TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

init_db()

class ConnectionManager:
    def __init__(self): self.active_connections = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
    def disconnect(self, ws: WebSocket): self.active_connections.remove(ws)
    async def broadcast(self, msg: str):
        for conn in self.active_connections: await conn.send_text(msg)

manager = ConnectionManager()

@app.get("/")
async def get_index(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/login")
async def get_login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...)):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?)', (username.strip().lower(), "Привет!", "Не указана"))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=username.strip().lower())
    return resp

@app.get("/profile")
async def get_profile(request: Request):
    user = request.cookies.get("username")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bio, birthday FROM users WHERE username = ?', (user,))
    data = cursor.fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "username": user, "bio": data[0], "birthday": data[1]})

@app.get("/edit")
async def get_edit(request: Request):
    user = request.cookies.get("username")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bio, birthday FROM users WHERE username = ?', (user,))
    data = cursor.fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "bio": data[0], "birthday": data[1]})

@app.post("/edit")
async def post_edit(request: Request, bio: str = Form(...), birthday: str = Form(...)):
    user = request.cookies.get("username")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET bio = ?, birthday = ? WHERE username = ?', (bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

@app.websocket("/ws/{username}")
async def ws_endpoint(ws: WebSocket, username: str):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
