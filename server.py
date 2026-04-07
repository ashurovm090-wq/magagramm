import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import sqlite3

app = FastAPI()

# Подключаем шаблоны (файлы .html должны лежать в той же папке)
templates = Jinja2Templates(directory=".")

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT
        )
    ''')
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Запускаем создание БД при старте
init_db()

# --- МАРШРУТЫ (ROUTES) ---

# 1. Страница входа (Login)
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 2. Главная страница - ЧАТ
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    # Тут можно будет подгружать сообщения из БД
    return templates.TemplateResponse("chat.html", {"request": request})

# 3. Поиск пользователей
@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

# 4. Профиль
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    # Пример данных пользователя
    user_data = {"username": "Мухаммад Ашуров", "email": "ashurovm090@gmail.com"}
    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})

# 5. Редактирование профиля
@app.get("/edit", response_class=HTMLResponse)
async def edit_page(request: Request):
    return templates.TemplateResponse("edit.html", {"request": request})

# --- ЗАПУСК СЕРВЕРА (ДЛЯ RENDER) ---
if __name__ == "__main__":
    # Берем порт из переменной окружения Render или ставим 8000 для локалки
    port = int(os.environ.get("PORT", 8000))
    # host="0.0.0.0" ОБЯЗАТЕЛЕН для деплоя
    uvicorn.run(app, host="0.0.0.0", port=port)
