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

# Главная — теперь перекидывает в профиль, если юзер залогинен
@app.get("/")
def index(request: Request):
    user = request.cookies.get("username")
    if user:
        return RedirectResponse(url="/profile")
    return templates.TemplateResponse("login.html", {"request": request})

# Обработка входа/регистрации
@app.post("/login")
def login(username: str = Form(...), fullname: str = Form(None), bio: str = Form(None), birthday: str = Form(None)):
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO users (username, fullname, bio, birthday) VALUES (?, ?, ?, ?)', 
                 (username.lower(), fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

# Профиль
@app.get("/profile")
def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

# Поиск — новый маршрут
@app.get("/search")
def search(request: Request):
    conn = get_db()
    all_users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return templates.TemplateResponse("search.html", {"request": request, "users": all_users})

# Редактирование — новый маршрут
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
