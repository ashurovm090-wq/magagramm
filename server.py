from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()
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
    user = request.cookies.get("username")
    if user: return RedirectResponse(url="/profile")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...)):
    username = username.lower().strip()
    conn = get_db()
    # Проверяем, есть ли юзер, если нет - создаем пустую запись
    user_exists = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user_exists:
        conn.execute('INSERT INTO users (username, fullname, bio, birthday) VALUES (?, ?, ?, ?)', 
                     (username, username, "", ""))
        conn.commit()
    conn.close()
    
    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(key="username", value=username)
    return resp

# НОВЫЙ МЕТОД ДЛЯ СОХРАНЕНИЯ ДАННЫХ
@app.post("/update_profile")
def update_profile(request: Request, fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    
    conn = get_db()
    conn.execute('UPDATE users SET fullname = ?, bio = ?, birthday = ? WHERE username = ?', 
                 (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

@app.get("/profile")
def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

@app.get("/search")
def search(request: Request):
    conn = get_db()
    all_users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return templates.TemplateResponse("search.html", {"request": request, "users": all_users})

@app.get("/edit")
def edit_page(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "user": u})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
