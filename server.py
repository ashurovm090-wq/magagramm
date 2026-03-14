from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from contextlib import asynccontextmanager

# Современный способ запуска (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)')
    conn.commit()
    conn.close()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO users (username, fullname, bio, birthday) VALUES (?, ?, ?, ?)', 
                 (username.lower(), fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

@app.get("/profile")
async def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    if not u: return RedirectResponse(url="/")
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})
