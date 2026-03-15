import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, 
            fullname TEXT, 
            bio TEXT, 
            birthday TEXT, 
            password TEXT
        )
    ''')
    cur.execute('CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, sender TEXT, receiver TEXT, text TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def index(request: Request):
    user = request.cookies.get("username")
    if user: return RedirectResponse(url="/search")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    username = username.lower().strip()
    # Обрезаем пароль до 72 символов
    safe_password = password[:72]
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_record = cur.fetchone()
    
    if not user_record:
        # Регистрация нового пользователя
        hashed_pw = pwd_context.hash(safe_password)
        cur.execute(
            'INSERT INTO users (username, fullname, bio, birthday, password) VALUES (%s, %s, %s, %s, %s)', 
            (username, username, "", "", hashed_pw)
        )
        conn.commit()
    else:
        # Проверка пароля с учетом старых аккаунтов (без пароля)
        if user_record.get('password'):
            # Если пароль есть — проверяем
            if not pwd_context.verify(safe_password, user_record['password']):
                conn.close()
                return "Ошибка: Неверный пароль."
        else:
            # Если пароля в базе нет — привязываем текущий введенный
            hashed_pw = pwd_context.hash(safe_password)
            cur.execute('UPDATE users SET password = %s WHERE username = %s', (hashed_pw, username))
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
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (user,))
    u = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("profile.html", {"request": request, "user": u})

@app.get("/chats")
def list_chats(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT sender as interlocutor FROM messages WHERE receiver = %s
        UNION
        SELECT DISTINCT receiver as interlocutor FROM messages WHERE sender = %s
    """, (user, user))
    chats = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("chats.html", {"request": request, "chats": chats})

@app.get("/edit")
def edit_page(request: Request):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (user,))
    u = cur.fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "user": u})

@app.get("/search")
def search(request: Request):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    all_users = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("search.html", {"request": request, "users": all_users})

@app.get("/chat/{interlocutor}")
def get_chat(request: Request, interlocutor: str):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM messages WHERE (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s) ORDER BY id ASC", 
                       (user, interlocutor, interlocutor, user))
    msgs = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("chat.html", {"request": request, "messages": msgs, "receiver": interlocutor, "me": user})

@app.post("/send_message")
def send_msg(receiver: str = Form(...), text: str = Form(...), request: Request = None):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender, receiver, text) VALUES (%s, %s, %s)", (user, receiver, text))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/chat/{receiver}", status_code=303)

@app.post("/update_profile")
def update_profile(request: Request, fullname: str = Form(...), bio: str = Form(...), birthday: str = Form(...)):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/")
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE users SET fullname = %s, bio = %s, birthday = %s WHERE username = %s', (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
