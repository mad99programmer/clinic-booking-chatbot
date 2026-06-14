from fastapi import FastAPI, Form, Depends, Request
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base
from handlers import process_message
from messaging import send_reply
from fastapi.staticfiles import StaticFiles
from admin_routes import router as admin_router
from auth_routes import router as auth_router
# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(bind=engine)


#temporary admin creation


from models import Admin
from security import hash_password

db = SessionLocal()

try:
    admin = db.query(Admin).filter(
        Admin.username == "admin"
    ).first()

    if not admin:
        admin = Admin(
            username="admin",
            password_hash=hash_password("Admin@123")
        )

        db.add(admin)
        db.commit()

finally:
    db.close()

app = FastAPI()

app.include_router(admin_router)
app.include_router(auth_router)
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
async def webhook_twilio(
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
# Zernio WEBHOOK
# =========================
@app.post("/webhook/zernio")
async def webhook_zernio(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    print("RAW PAYLOAD:", payload)

    if payload.get("event") == "message.received":
        message = payload.get("message", {})
        account = payload.get("account", {})

        user_number = message.get("sender", {}).get("phoneNumber")
        incoming_msg = message.get("text", "").strip()
        conversation_id = message.get("conversationId")
        account_id = account.get("id")

        reply = process_message(user_number, incoming_msg, db, webhook_data=message)
        send_reply(conversation_id, account_id, reply)

    return {"status": "ok"}




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

@app.get("/run-slot-generator")
def run_slot_generator():
    from slot_generator import generate_slots_for_next_7_days
    generate_slots_for_next_7_days()
    return {"status": "slots generated"}