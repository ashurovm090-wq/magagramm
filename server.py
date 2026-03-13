from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Добавляем поля: ФИО, bio, день рождения
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

init_db()

active_connections = {}

@app.get("/login")
async def get_login(request: Request): 
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(
    username: str = Form(...), 
    fullname: str = Form(...), 
    bio: str = Form(...), 
    birthday: str = Form(...)
):
    clean_user = username.strip().lower()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Используем INSERT OR REPLACE, чтобы обновлять данные при повторном входе
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', 
                   (clean_user, fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=clean_user)
    return resp

# Остальные роуты (профиль, поиск, чат) остаются, но теперь они будут брать данные из новых полей
