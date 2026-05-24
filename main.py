from fastapi import FastAPI, Form, Depends
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base
from handlers import process_message
from messaging import send_reply
from fastapi.staticfiles import StaticFiles
from admin_routes import router as admin_router

# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(admin_router)
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")
# =========================
# DATABASE SESSION
# =========================
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
async def health_check():

    return {
        "status": "I am alive"
    }


# =========================
# TWILIO WEBHOOK
# =========================
@app.post("/webhook")
async def webhook(
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):

    user_number = From.replace("whatsapp:", "")

    incoming_msg = Body.strip()

    reply = process_message(
        user_number,
        incoming_msg,
        db
    )

    send_reply(user_number, reply)

    return {
        "status": "ok"
    }


# =========================
# LOCAL TEST ENDPOINT
# =========================
@app.get("/test")
async def test_chat(
    msg: str,
    user: str = "9999999999",
    db: Session = Depends(get_db)
):

    reply = process_message(
        user,
        msg,
        db
    )

    return {
        "user_message": msg,
        "bot_reply": reply
    }