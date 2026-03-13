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

active_connections = {}

@app.get("/")
async def get_index(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/login")
async def get_login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...)):
    clean_user = username.strip().lower()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?)', (clean_user, "Привет!", "Не указана"))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=clean_user)
    return resp

@app.get("/profile")
async def get_profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bio, birthday FROM users WHERE username = ?', (user,))
    data = cursor.fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {
        "request": request, "username": user, 
        "bio": data[0] if data else "Привет!", "birthday": data[1] if data else "Не указана"
    })

@app.get("/search")
async def search_users(query: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()
    return {"users": [r[0] for r in results]}

@app.websocket("/ws/{username}")
async def ws_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            for connection in active_connections.values():
                await connection.send_text(f"{username}: {data}")
    except WebSocketDisconnect:
        del active_connections[username]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
