from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

# Инициализация БД
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, bio TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Менеджер чата (WebSocket)
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

# --- РОУТЫ ---

@app.get("/")
async def get_index(request: Request):
    username = request.cookies.get("username")
    if not username: return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...)):
    clean_username = username.strip().lower()
    # Запись в БД при первом входе
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (username, bio, birthday) VALUES (?, ?, ?)', 
                   (clean_username, "Привет, я в Magagrame!", "Не указана"))
    conn.commit()
    conn.close()
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="username", value=clean_username)
    return response

@app.get("/profile")
async def get_profile(request: Request):
    username = request.cookies.get("username")
    if not username: return RedirectResponse(url="/login")
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bio, birthday FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    bio = user[0] if user else "Привет, я новенький!"
    bday = user[1] if user else "Не указана"
    
    return templates.TemplateResponse("profile.html", {
        "request": request, "username": username, "bio": bio, "birthday": bday
    })

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"--- {username} покинул чат ---")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
