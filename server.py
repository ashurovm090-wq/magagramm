from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import os, json, sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("database.db")
    # База для ЛС: от кого, кому, текст
    conn.execute("CREATE TABLE IF NOT EXISTS msgs (from_user TEXT, to_user TEXT, text TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE)")
    conn.commit()
    conn.close()

init_db()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]

    async def send_private(self, message: str, to_user: str):
        if to_user in self.active_connections:
            await self.active_connections[to_user].send_text(message)

manager = ConnectionManager()

def serve_html(name: str):
    if os.path.exists(name):
        with open(name, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="404", status_code=404)

@app.get("/")
async def index(): return serve_html("index.html")
@app.get("/chats")
async def chats(): return serve_html("chats.html")
@app.get("/chat")
async def chat(): return serve_html("chat.html")
@app.get("/profile")
async def profile(): return serve_html("profile.html")
@app.get("/edit")
async def edit(): return serve_html("edit.html")

@app.get("/api/users")
async def get_users():
    conn = sqlite3.connect("database.db")
    res = conn.execute("SELECT username FROM users").fetchall()
    conn.close()
    return [r[0] for r in res]

@app.get("/api/messages")
async def get_messages(me: str, with_user: str):
    conn = sqlite3.connect("database.db")
    cur = conn.execute("SELECT from_user, text FROM msgs WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)", (me, with_user, with_user, me))
    data = [{"u": r[0], "t": r[1]} for r in cur.fetchall()]
    conn.close()
    return data

@app.post("/api/register")
async def register(user: str):
    conn = sqlite3.connect("database.db")
    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (user,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.websocket("/ws/{user}")
async def websocket_endpoint(websocket: WebSocket, user: str):
    await manager.connect(user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            conn = sqlite3.connect("database.db")
            conn.execute("INSERT INTO msgs (from_user, to_user, text) VALUES (?, ?, ?)", (user, msg['to'], msg['t']))
            conn.commit()
            conn.close()
            await manager.send_private(json.dumps({"u": user, "t": msg['t']}), msg['to'])
            await websocket.send_text(json.dumps({"u": user, "t": msg['t']}))
    except WebSocketDisconnect:
        manager.disconnect(user)
