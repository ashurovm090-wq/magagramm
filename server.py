from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import os, json, sqlite3

app = FastAPI()

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Таблица для истории сообщений
    cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user TEXT, text TEXT)")
    # Таблица для пользователей (чтобы поиск их видел)
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
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def serve_html(file_name: str):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>404: Файл не найден</h1>", status_code=404)

# Навигация
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

# API: Получение истории сообщений из базы
@app.get("/api/messages")
async def get_messages():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user, text FROM msgs")
    data = [{"u": r[0], "t": r[1]} for r in cursor.fetchall()]
    conn.close()
    return data

# API: Регистрация пользователя в базе для поиска
@app.post("/api/register")
async def register(user: str):
    conn = sqlite3.connect("database.db")
    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (user,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# WebSocket: Обработка живого чата
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            # Сохраняем сообщение в базу данных, чтобы оно не пропадало
            conn = sqlite3.connect("database.db")
            conn.execute("INSERT INTO msgs (user, text) VALUES (?, ?)", (msg['u'], msg['t']))
            conn.commit()
            conn.close()
            
            # Рассылаем сообщение всем пользователям онлайн
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
