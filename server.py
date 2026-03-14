from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory=".")

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/update_profile")
async def update_profile(
    request: Request,
    fullname: str = Form(...),
    bio: str = Form(...),
    birthday: str = Form(...)
):
    user = request.cookies.get("username")
    if not user: return RedirectResponse(url="/login")
    
    conn = get_db()
    conn.execute('UPDATE users SET fullname=?, bio=?, birthday=? WHERE username=?', 
                 (fullname, bio, birthday, user))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/profile", status_code=303)

# Оставляем остальные методы (GET /profile, GET /edit и т.д.) без изменений
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
