from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import re

app = FastAPI()
templates = Jinja2Templates(directory=".")

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
    # Убираем пробелы и переводим в нижний регистр
    clean_username = username.strip().lower()
    
    # ПРОВЕРКА: только латинские буквы (a-z) и цифры (0-9)
    # Если в нике есть что-то другое, вернем ошибку
    if not re.match("^[a-z0-9]+$", clean_username):
        return HTMLResponse("Ошибка! Используй только английские буквы и цифры.", status_code=400)
    
    response = RedirectResponse(url="/", status_code=303)
    # Сохраняем чистый ник в куки
    response.set_cookie(key="username", value=clean_username, max_age=2592000)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
