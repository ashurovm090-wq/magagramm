from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# --- Инициализация базы данных ---
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db()
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, text TEXT)')
conn.commit()
conn.close()

@app.get("/")
def index(request: Request):
    user = request.cookies.get("username")
    if user: return RedirectResponse(url="/search")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...)):
    username = username.lower().strip()
    conn = get_db()
    if not conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
        conn.execute('INSERT INTO users (username, fullname, bio, birthday) VALUES (?, ?, ?, ?)', (username, username, "", ""))
        conn.commit()
    conn.close()
    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(key="username", value=username)
    return resp

@app.get("/profile")
def profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

@app.get("/edit")
def edit_page(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "user": u})

@app.get("/search")
def search(request: Request):
    conn = get_db()
    all_users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return templates.TemplateResponse("search.html", {"request": request, "users": all_users})

@app.get("/chat/{interlocutor}")
def get_chat(request: Request, interlocutor: str):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    msgs = conn.execute("SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id ASC", 
                       (user, interlocutor, interlocutor, user)).fetchall()
    conn.close()
    return templates.TemplateResponse("chat.html", {"request": request, "messages": msgs, "receiver": interlocutor, "me": user})

@app.post("/send_message")
def send_msg(receiver: str = Form(...), text: str = Form(...), request: Request = None):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    conn.execute("INSERT INTO messages (sender, receiver, text) VALUES (?, ?, ?)", (user, receiver, text))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/chat/{receiver}", status_code=303)

@app.post("/update_profile")
def update_profile(request: Request, fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    conn.execute('UPDATE users SET fullname = ?, bio = ?, birthday = ? WHERE username = ?', (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
