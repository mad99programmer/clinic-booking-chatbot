# main.py

import re
import os

from fastapi import FastAPI, Form, Depends
from sqlalchemy.orm import Session
from twilio.rest import Client
from dotenv import load_dotenv

from database import engine, SessionLocal
from models import Base, User, UserSession, Doctor, DoctorSlot,Appointment


# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(bind=engine)


# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

app = FastAPI()


# =========================
# TWILIO CONFIG
# =========================
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

FROM_NUMBER = "whatsapp:+14155238886"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

TEST_MODE = True


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
# DISPLAY MENU
# =========================
def display_menu():

    return (
        "👋 Welcome to City Clinic!\n\n"
        "Please choose an option:\n\n"
        "1️⃣ Book Appointment\n"
        "2️⃣ Cancel Appointment\n"
        "3️⃣ Clinic Hours\n"
        "4️⃣ Location"
    )


# =========================
# FETCH SPECIALIZATIONS
# =========================
def get_specializations(db):

    specializations = db.query(
        Doctor.specialization
    ).distinct().all()

    return [s[0] for s in specializations]

# =========================
# FETCH DOCTORS BASED ON SELECTED SPECIALIZATIONS
# =========================
def get_doctors_by_specialization(
    db,
    specialization
):

    return db.query(Doctor).filter(
        Doctor.specialization == specialization,
        Doctor.is_active == True
    ).all()

# =========================
#  GET AVAILABLE DATES FOR THE SELECTED DOCTOR
# =========================
def get_available_dates(
    db,
    doctor_id
):

    slots = db.query(
        DoctorSlot.slot_date
    ).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == "available"
    ).distinct().all()

    return [slot[0] for slot in slots]

# =========================
#  GET AVAILABLE DATES FOR THE SELECTED DOCTOR BASED ON SELECTED DATE
# =========================

def get_available_slots(
    db,
    doctor_id,
    slot_date
):

    return db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.slot_date == slot_date,
        DoctorSlot.status == "available"
    ).all()
# =========================
# NAME VALIDATION
# =========================
def is_valid_name(name: str) -> bool:

    name = name.strip()

    if len(name) < 2 or len(name) > 60:
        return False

    if not re.match(r"^[A-Za-z\s.\-']+$", name):
        return False

    return True


# =========================
# EMAIL VALIDATION
# =========================
def is_valid_email(email: str) -> bool:

    return bool(
        re.match(
            r"^[\w\.-]+@[\w\.-]+\.\w{2,}$",
            email.strip()
        )
    )


# =========================
# SEND WHATSAPP MESSAGE
# =========================
def send_reply(to: str, message: str):

    if TEST_MODE:

        print("\nBOT REPLY:")
        print(message)

    else:

        client.messages.create(
            from_=FROM_NUMBER,
            to=f"whatsapp:{to}",
            body=message
        )


# =========================
# PROCESS MESSAGE
# =========================
def process_message(
    user_number,
    incoming_msg,
    db
):

    normalized_msg = incoming_msg.lower()

    MENU_COMMANDS = [
        "hi",
        "hello",
        "hey",
        "menu",
        "hie",
        "1",
        "2",
        "3",
        "4"
    ]

    # =========================
    # FETCH SESSION
    # =========================
    session = db.query(UserSession).filter(
        UserSession.phone_number == user_number
    ).first()


# =========================
# GLOBAL MENU RESET
# =========================
    if normalized_msg in [
        "hi",
        "hello",
        "hey",
        "menu",
        "home",
        "reset"
    ]:

        if session:

            session.current_step = "idle"

            session.temp_name = None
            session.temp_email = None
            session.temp_gender = None

            session.selected_specialization = None
            session.selected_doctor_id = None
            session.selected_slot_id = None
            session.selected_date = None

            db.commit()

        return display_menu()

    # =========================
    # HANDLE NAME COLLECTION
    # =========================
    if session and session.current_step == "collecting_name":

        if normalized_msg in MENU_COMMANDS:

            reply = (
                "👤 Please enter your full name first "
                "to continue booking."
            )

        elif not is_valid_name(incoming_msg):

            reply = (
                "⚠️ That doesn't look like a valid name.\n\n"
                "Please enter your full name.\n"
                "Example: John Doe"
            )

        else:

            session.temp_name = incoming_msg.strip()

            session.current_step = "collecting_email"

            db.commit()

            reply = (
                f"✅ Got it, {session.temp_name}!\n\n"
                "Please enter your email address."
            )

    # =========================
    # HANDLE EMAIL COLLECTION
    # =========================
    elif session and session.current_step == "collecting_email":

        if normalized_msg in MENU_COMMANDS:

            reply = (
                "📧 Please enter your email address first."
            )

        elif not is_valid_email(incoming_msg):

            reply = (
                "⚠️ Invalid email address.\n\n"
                "Example: john@example.com"
            )

        else:

            session.temp_email = incoming_msg.strip().lower()

            session.current_step = "collecting_gender"

            db.commit()

            reply = (
                "Please select your gender:\n\n"
                "1️⃣ Male\n"
                "2️⃣ Female\n"
                "3️⃣ Prefer not to say"
            )

    # =========================
    # HANDLE GENDER COLLECTION
    # =========================
    elif session and session.current_step == "collecting_gender":

        gender_map = {
            "1": "Male",
            "2": "Female",
            "3": "Prefer not to say"
        }

        if normalized_msg not in gender_map:

            reply = (
                "Please reply with:\n\n"
                "1️⃣ Male\n"
                "2️⃣ Female\n"
                "3️⃣ Prefer not to say"
            )

        else:

            session.temp_gender = gender_map[
                normalized_msg
            ]

            session.current_step = "confirming_details"

            db.commit()

            reply = (
                f"Please confirm your details:\n\n"
                f"👤 Name: {session.temp_name}\n"
                f"📧 Email: {session.temp_email}\n"
                f"⚧ Gender: {session.temp_gender}\n\n"
                f"1️⃣ Yes, confirm\n"
                f"2️⃣ No, start over"
            )

    # =========================
    # HANDLE DETAILS CONFIRMATION
    # =========================
    elif session and session.current_step == "confirming_details":

        # YES
        if normalized_msg == "1":

            new_user = User(
                phone_number=user_number,
                name=session.temp_name,
                email=session.temp_email,
                gender=session.temp_gender
            )

            db.add(new_user)

            session.temp_name = None
            session.temp_email = None
            session.temp_gender = None

            session.current_step = (
                "selecting_specialization"
            )

            db.commit()

            specializations = get_specializations(db)

            specialization_text = ""

            for index, specialization in enumerate(
                specializations,
                start=1
            ):

                specialization_text += (
                    f"{index}️⃣ {specialization}\n"
                )

            reply = (
                f"✅ Registration completed!\n\n"
                f"Welcome {new_user.name} 👋\n\n"
                f"Choose specialization:\n\n"
                f"{specialization_text}"
            )

        # NO
        elif normalized_msg == "2":

            session.temp_name = None
            session.temp_email = None
            session.temp_gender = None

            session.current_step = (
                "collecting_name"
            )

            db.commit()

            reply = (
                "No problem!\n\n"
                "Please enter your full name."
            )

        else:

            reply = (
                "Please reply with:\n\n"
                "1️⃣ Yes, confirm\n"
                "2️⃣ No, start over"
            )
    # =========================
    # HANDLE SPECIALIZATION SELECTION
    # =========================
    elif session and session.current_step == "selecting_specialization":
        
        specializations = get_specializations(db)
        # validate option
        if not normalized_msg.isdigit():

            reply = (
                "Please enter a valid specialization number."
            )
        else:
            selected_index = int(normalized_msg) - 1

            if ( selected_index < 0 or selected_index >= len(specializations)):

                    reply = (
                        "Invalid specialization selection."
                    )
            else:

                selected_specialization = (
                    specializations[selected_index]
                )

                session.selected_specialization = (
                    selected_specialization
                )

                session.current_step = (
                    "selecting_doctor"
                )

                db.commit()

                doctors = get_doctors_by_specialization(
                    db,
                    selected_specialization
                )

                doctor_text = ""

                for index, doctor in enumerate(
                    doctors,
                    start=1
                ):

                    doctor_text += (
                        f"{index}️⃣ "
                        f"{doctor.name}\n"
                    )

                reply = (
                    f"Available doctors for "
                    f"{selected_specialization}:\n\n"
                    f"{doctor_text}"
                )

    # =========================
    # HANDLE DOCTOR SELECTION
    # =========================
    elif session and session.current_step == "selecting_doctor":

        doctors = get_doctors_by_specialization(
            db,
            session.selected_specialization
        )

        # validate input
        if not normalized_msg.isdigit():

            reply = (
                "Please enter a valid doctor number."
            )

        else:

            selected_index = int(normalized_msg) - 1

            if (
                selected_index < 0
                or selected_index >= len(doctors)
            ):

                reply = (
                    "Invalid doctor selection."
                )

            else:

                selected_doctor = doctors[
                    selected_index
                ]

                session.selected_doctor_id = (
                    selected_doctor.id
                )

                session.current_step = (
                    "selecting_date"
                )

                db.commit()

                available_dates = get_available_dates(
                    db,
                    selected_doctor.id
                )

                if not available_dates:

                    reply = (
                        "No slots available currently."
                    )

                else:

                    date_text = ""

                    for index, slot_date in enumerate(
                        available_dates,
                        start=1
                    ):

                        formatted_date = (
                            slot_date.strftime(
                                "%d %B %Y"
                            )
                        )

                        date_text += (
                            f"{index}️⃣ "
                            f"{formatted_date}\n"
                        )

                    reply = (
                        f"Available dates for "
                        f"{selected_doctor.name}:\n\n"
                        f"{date_text}"
                    )
    # =========================
    # HANDLE DATE SELECTION
    # =========================
    elif session and session.current_step == "selecting_date":

        available_dates = get_available_dates(
            db,
            session.selected_doctor_id
        )

        # validate input
        if not normalized_msg.isdigit():

            reply = (
                "Please enter a valid date number."
            )

        else:

            selected_index = int(normalized_msg) - 1

            if (
                selected_index < 0
                or selected_index >= len(available_dates)
            ):

                reply = (
                    "Invalid date selection."
                )

            else:

                selected_date = available_dates[
                    selected_index
                ]

                session.selected_date = selected_date

                session.current_step = (
                    "selecting_slot"
                )

                db.commit()

                slots = get_available_slots(
                    db,
                    session.selected_doctor_id,
                    selected_date
                )

                slot_text = ""

                for index, slot in enumerate(
                    slots,
                    start=1
                ):

                    start_time = slot.start_time.strftime(
                        "%I:%M %p"
                    )

                    end_time = slot.end_time.strftime(
                        "%I:%M %p"
                    )

                    slot_text += (
                        f"{index}️⃣ "
                        f"{start_time} - {end_time}\n"
                    )

                reply = (
                    f"Available slots:\n\n"
                    f"{slot_text}"
                )

    # =========================
    # HANDLE SLOT SELECTION
    # =========================
    elif session and session.current_step == "selecting_slot":

        slots = get_available_slots(
            db,
            session.selected_doctor_id,
            session.selected_date
        )

        # validate input
        if not normalized_msg.isdigit():

            reply = (
                "Please enter a valid slot number."
            )

        else:

            selected_index = int(normalized_msg) - 1

            if (
                selected_index < 0
                or selected_index >= len(slots)
            ):

                reply = (
                    "Invalid slot selection."
                )

            else:

                selected_slot = slots[
                    selected_index
                ]

                # prevent double booking
                if selected_slot.status != "available":

                    reply = (
                        "Sorry, this slot "
                        "was just booked."
                    )

                else:

                    # mark slot booked
                    selected_slot.status = "booked"

                    # fetch user
                    user = db.query(User).filter(
                        User.phone_number == user_number
                    ).first()

                    # create appointment
                    appointment = Appointment(
                        user_id=user.id,
                        doctor_id=session.selected_doctor_id,
                        slot_id=selected_slot.id,
                        appointment_date=selected_slot.slot_date,
                        status="booked"
                    )

                    db.add(appointment)

                    # reset session
                    session.current_step = "idle"

                    session.selected_specialization = None
                    session.selected_doctor_id = None
                    session.selected_date = None

                    db.commit()

                    # fetch doctor
                    doctor = db.query(Doctor).filter(
                        Doctor.id == appointment.doctor_id
                    ).first()

                    formatted_date = (
                        selected_slot.slot_date.strftime(
                            "%d %B %Y"
                        )
                    )

                    start_time = (
                        selected_slot.start_time.strftime(
                            "%I:%M %p"
                        )
                    )

                    reply = (
                        f"✅ Appointment booked!\n\n"
                        f"👨‍⚕️ Doctor: {doctor.name}\n"
                        f"📅 Date: {formatted_date}\n"
                        f"⏰ Time: {start_time}\n\n"
                        f"Thank you!"
                    )





    # =========================
    # MAIN MENU
    # =========================
    elif normalized_msg in [
        "hi",
        "hello",
        "hey",
        "menu",
        "hie"
    ]:

        reply = display_menu()

    # =========================
    # BOOK APPOINTMENT
    # =========================
    elif normalized_msg == "1":

        user = db.query(User).filter(
            User.phone_number == user_number
        ).first()

        if not session:

            session = UserSession(
                phone_number=user_number,
                current_step="idle"
            )

            db.add(session)

            db.commit()

            db.refresh(session)

        # NEW USER
        if not user:

            session.current_step = (
                "collecting_name"
            )

            db.commit()

            reply = (
                "👋 Welcome to City Clinic!\n\n"
                "Let's get you registered first.\n\n"
                "Please enter your full name."
            )

        # EXISTING USER
        else:

            specializations = get_specializations(db)

            session.current_step = (
                "selecting_specialization"
            )

            db.commit()

            specialization_text = ""

            for index, specialization in enumerate(
                specializations,
                start=1
            ):

                specialization_text += (
                    f"{index}️⃣ {specialization}\n"
                )

            reply = (
                f"Welcome back {user.name} 👋\n\n"
                f"Choose specialization:\n\n"
                f"{specialization_text}"
            )

    # =========================
    # CANCEL APPOINTMENT
    # =========================
    elif normalized_msg == "2":

        reply = (
            "Please share your appointment ID "
            "or registered phone number to cancel."
        )

    # =========================
    # CLINIC HOURS
    # =========================
    elif normalized_msg == "3":

        reply = (
            "🕐 We're open Mon–Sat, "
            "9 AM to 7 PM.\n"
            "Sunday: 10 AM to 2 PM."
        )

    # =========================
    # LOCATION
    # =========================
    elif normalized_msg == "4":

        reply = (
            "📍 123 Health Street, "
            "Near Central Park.\n"
            "Google Maps: "
            "https://maps.google.com/?q=..."
        )

    # =========================
    # UNKNOWN MESSAGE
    # =========================
    else:

        reply = (
            "Sorry, I didn't understand that.\n\n"
            "Reply *hi* to see the menu."
        )

    return reply


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

    user_number = From.replace(
        "whatsapp:",
        ""
    )

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