from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

def get_db_conn():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
async def startup():
    conn = get_db_conn()
    # Создаем таблицу с датой рождения
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (username TEXT PRIMARY KEY, fullname TEXT, bio TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

# --- РОУТЫ ---

@app.get("/")
async def get_index(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/login")
async def get_login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...), fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    conn = get_db_conn()
    conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', (username.lower(), fullname, bio, birthday))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="username", value=username.lower())
    return resp

@app.get("/profile")
async def get_profile(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    conn = get_db_conn()
    user_data = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})

@app.get("/edit")
async def get_edit(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    conn = get_db_conn()
    user_data = conn.execute("SELECT * FROM users WHERE username = ?", (user,)).fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "user": user_data})

@app.post("/update_profile")
async def update_profile(request: Request, fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    user = request.cookies.get("username")
    conn = get_db_conn()
    conn.execute('UPDATE users SET fullname=?, bio=?, birthday=? WHERE username=?', (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
