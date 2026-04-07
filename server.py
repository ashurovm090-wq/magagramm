from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Если у тебя есть папка со статикой (картинки, стили)
# app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    # Тут можно передать имя пользователя
    return templates.TemplateResponse("chat.html", {"request": request, "user": "Мухаммад"})

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
