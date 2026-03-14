from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
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
    user = request.cookies.get("username")
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/login")
def login_get(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(username: str = Form(...), fullname: str = Form(...)):
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO users (username, fullname) VALUES (?, ?)', (username.lower(), fullname))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

@app.get("/profile")
def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

@app.get("/edit")
def edit_get(request: Request):
    user = request.cookies.get("username")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "user": u})

@app.post("/update")
def update(fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...), request: Request = None):
    user = request.cookies.get("username")
    conn = get_db()
    conn.execute('UPDATE users SET fullname=?, bio=?, birthday=? WHERE username=?', (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)
