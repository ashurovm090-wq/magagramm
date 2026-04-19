from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import os, json, sqlite3

app = FastAPI()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user TEXT, text TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE)")
    conn.commit()
    conn.close()

init_db()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for conn in self.active_connections:
            await conn.send_text(message)

manager = ConnectionManager()

def serve_html(name: str):
    if os.path.exists(name):
        with open(name, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="404 Not Found", status_code=404)

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

@app.get("/api/messages")
async def get_messages():
    conn = sqlite3.connect("database.db")
    res = conn.execute("SELECT user, text FROM msgs").fetchall()
    conn.close()
    return [{"u": r[0], "t": r[1]} for r in res]

@app.post("/api/register")
async def register(user: str):
    conn = sqlite3.connect("database.db")
    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (user,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            conn = sqlite3.connect("database.db")
            conn.execute("INSERT INTO msgs (user, text) VALUES (?, ?)", (msg['u'], msg['t']))
            conn.commit()
            conn.close()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
