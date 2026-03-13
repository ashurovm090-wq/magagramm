from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import re

app = FastAPI()
templates = Jinja2Templates(directory=".")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, bio TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(username: str = Form(...)):
    clean_username = username.strip().lower()
    
    # Проверка: только латынь
    if not re.match("^[a-z0-9]+$", clean_username):
        return HTMLResponse("Ошибка: используй только английские буквы и цифры!", status_code=400)
    
    # Записываем юзера в БД, если его там нет
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (username, bio, birthday) VALUES (?, ?, ?)', 
                   (clean_username, "Привет, я в Magagrame!", "Не указана"))
    conn.commit()
    conn.close()
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="username", value=clean_username, max_age=2592000)
    return response

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login")
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bio, birthday FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    return templates.TemplateResponse("index.html", {"request": request, "username": username, "bio": user[0], "birthday": user[1]})

@app.get("/search")
async def get_search(q: str = ""):
    return {"status": "success", "search_query": q, "message": "Поиск будет работать через базу данных"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
