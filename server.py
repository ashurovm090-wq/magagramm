from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import os

app = FastAPI()
# Монтируем текущую папку для доступа к картинкам
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def startup():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)')
    conn.commit()
    conn.close()

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), fullname: str = Form(None), bio: str = Form(None), birthday: str = Form(None)):
    conn = get_db()
    # Используем INSERT OR REPLACE, чтобы обновить данные, если юзер уже есть
    conn.execute('INSERT OR REPLACE INTO users (username, fullname, bio, birthday) VALUES (?, ?, ?, ?)', 
                 (username.lower(), fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

@app.get("/profile")
def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

# Добавляем для локального теста, Render сам запустит сервер через Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
