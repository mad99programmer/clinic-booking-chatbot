from ai_receptionist import suggest_specialization
from models import User, UserSession, Doctor, Appointment, DoctorSlot
from crud import (
    get_specializations,
    get_doctors_by_specialization,
    get_available_dates,
    get_available_slots,
    get_available_sessions_v2
)
from validators import is_valid_name, is_valid_email, is_valid_age
from messaging import display_menu,build_specialization_list,build_doctor_list,build_date_list,build_session_list,build_slot_list_page
from datetime import date

from helpers import get_slots_for_selected_session,extract_payload
MENU_COMMANDS = [
    "hi",
    "hello",
    "hey",
    "menu",
    "hie",
    "1",
    "2",
    "3",
    "4",
    "5"
]



# =========================
# DISPLAY MENU
# =========================
def display_menu():
    return (
        "👋 Welcome to City Clinic!\n\n"
        "Please choose an option:\n\n"
        "1️⃣ Book Appointment\n"
        "2️⃣ Cancel Appointment\n"
        "3️⃣ My Appointments\n"
        "4️⃣ Clinic Hours\n"
        "5️⃣ Location"
    )


# =========================
# GET UPCOMING APPOINTMENTS
# =========================
def get_upcoming_appointments(user_number, db):

    user = db.query(User).filter(
        User.phone_number == user_number
    ).first()

    if not user:
        return []

    today = date.today()

    appointments = db.query(Appointment).filter(
        Appointment.user_id == user.id,
        Appointment.status == "booked",
        Appointment.appointment_date >= today
    ).order_by(
        Appointment.appointment_date
    ).all()

    result = []

    for appt in appointments:

        doctor = db.query(Doctor).filter(
            Doctor.id == appt.doctor_id
        ).first()

        slot = db.query(DoctorSlot).filter(
            DoctorSlot.id == appt.slot_id
        ).first()

        result.append({
            "id":           appt.id,
            "doctor_name":  doctor.name if doctor else "Unknown",
            "date":         appt.appointment_date.strftime("%d %B %Y"),
            "time":         slot.start_time.strftime("%I:%M %p") if slot else "",
            "slot_id":      appt.slot_id,
        })

    return result


# =========================
# FORMAT APPOINTMENTS TEXT
# =========================
def format_appointments(appointments):

    text = ""

    for index, appt in enumerate(appointments, start=1):

        text += (
            f"{index}️⃣ {appt['doctor_name']}\n"
            f"   📅 {appt['date']} at {appt['time']}\n\n"
        )

    return text


# =========================
# PROCESS MESSAGE
# =========================
def process_message(user_number, incoming_msg, db,webhook_data=None):

    normalized_msg = incoming_msg.lower().strip()
    interactive_payload = extract_payload(webhook_data)
    effective_input = interactive_payload or normalized_msg
    reply = (
        "Sorry, I didn't understand that.\n\n"
        "Reply *hi* to see the menu."
    )
    print(
        "TEXT:",
        incoming_msg,
        "PAYLOAD:",
        interactive_payload
    )
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
        "hi", "hello", "hey", "menu", "home", "reset","hie"
    ]:

        if session:

            session.current_step          = "idle"
            session.temp_name             = None
            session.temp_email            = None
            session.temp_gender           = None
            session.temp_age              = None
            session.selected_specialization = None
            session.selected_doctor_id    = None
            session.selected_slot_id      = None
            session.selected_date         = None
            session.selected_session      = None

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

            session.temp_gender = gender_map[normalized_msg]
            session.current_step = "collecting_age"
            db.commit()

            reply = (
                "Please enter your age.\n\n"
                "Example: 25"
            )

    # =========================
    # HANDLE AGE COLLECTION
    # =========================
    elif session and session.current_step == "collecting_age":

        if normalized_msg in MENU_COMMANDS:

            reply = (
                "🔢 Please enter your age to continue."
            )

        elif not is_valid_age(incoming_msg):

            reply = (
                "⚠️ Please enter a valid age.\n\n"
                "Example: 25"
            )

        else:

            session.temp_age = int(incoming_msg.strip())
            session.current_step = "confirming_details"
            db.commit()

            reply = (
                f"Please confirm your details:\n\n"
                f"👤 Name: {session.temp_name}\n"
                f"📧 Email: {session.temp_email}\n"
                f"⚧ Gender: {session.temp_gender}\n"
                f"🎂 Age: {session.temp_age}\n\n"
                f"1️⃣ Yes, confirm\n"
                f"2️⃣ No, start over"
            )

    # =========================
    # HANDLE DETAILS CONFIRMATION
    # =========================
    elif session and session.current_step == "confirming_details":

        if normalized_msg == "1":

            new_user = User(
                phone_number=user_number,
                name=session.temp_name,
                email=session.temp_email,
                gender=session.temp_gender,
                age=session.temp_age
            )

            db.add(new_user)

            session.temp_name             = None
            session.temp_email            = None
            session.temp_gender           = None
            session.temp_age              = None
            session.current_step          = "selecting_specialization"

            db.commit()

            specializations = get_specializations(db)
            specialization_text = ""

            for index, specialization in enumerate(
                specializations, start=1
            ):
                specialization_text += f"{index}️⃣ {specialization}\n"

            specialization_text += (
                f"{len(specializations)+1}️⃣ "
                f"Consult our AI Medical Receptionist\n"
            )

            reply = (
                f"✅ Registration completed!\n\n"
                f"Welcome {new_user.name} 👋\n\n"
                f"Choose specialization:\n\n"
                f"{specialization_text}"
            )

        elif normalized_msg == "2":

            session.temp_name             = None
            session.temp_email            = None
            session.temp_gender           = None
            session.temp_age              = None
            session.current_step          = "collecting_name"

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

        payload = effective_input

    
        # AI receptionist selected
        if payload == "ai_receptionist":

            session.current_step = "ai_symptom_collection"
            db.commit()

            reply = "🤖 Please describe your symptoms."

        # Manual specialization selected
        elif payload.startswith("specialization_"):

            selected_index = int(
                payload.replace(
                    "specialization_",
                    ""
                )
            )



            selected_specialization = (
                specializations[selected_index]
            )

            session.selected_specialization = (
                selected_specialization
            )
            session.current_step = "selecting_doctor"
            db.commit()

            doctors = get_doctors_by_specialization(
                db, selected_specialization
            )

            reply = build_doctor_list(
                doctors
            )
        else:

            reply = (
                "Invalid specialization selection."
            )

    # =========================
    # HANDLE AI SYMPTOM COLLECTION
    # =========================
    elif (
        session and
        session.current_step == "ai_symptom_collection"
    ):

        specializations = get_specializations(db)

        ai_result = suggest_specialization(
            incoming_msg,
            specializations
        )

        suggested_specialization = (
            ai_result["assigned_specialization"]
        )

        session.current_step = "selecting_specialization"
        db.commit()

        specialization_text = ""

        for index, specialization in enumerate(
            specializations, start=1
        ):

            if specialization == suggested_specialization:
                specialization_text += (
                    f"{index}️⃣ {specialization} ⭐ Recommended\n"
                )
            else:
                specialization_text += (
                    f"{index}️⃣ {specialization}\n"
                )

        specialization_text += (
            f"{len(specializations)+1}️⃣ "
            f"Consult our AI Medical Receptionist\n"
        )

        reply = (
            f"🤖 Based on your symptoms, "
            f"we recommend:\n\n"
            f"🏥 {suggested_specialization}\n\n"
            f"Please choose specialization:\n\n"
            f"{specialization_text}"
        )

    # =========================
    # HANDLE DOCTOR SELECTION
    # =========================
    elif session and session.current_step == "selecting_doctor":

        doctors = get_doctors_by_specialization(
            db,
            session.selected_specialization
        )

        payload = effective_input

        if not payload.startswith("doctor_"):

            reply = "Invalid doctor selection."

        else:

            doctor_id = int(
                payload.replace(
                    "doctor_",
                    ""
                )
            )

            selected_doctor = next(
                (
                    doctor
                    for doctor in doctors
                    if doctor.id == doctor_id
                ),
                None
            )

            if not selected_doctor:

                reply = "Invalid doctor selection."

            else:

                session.selected_doctor_id = selected_doctor.id
                session.current_step = "selecting_date"

                db.commit()

                available_dates = get_available_dates(
                    db,
                    selected_doctor.id
                )

                if not available_dates:

                    session.current_step = "selecting_specialization"
                    session.selected_doctor_id = None

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

                    specialization_text += (
                        f"{len(specializations)+1}️⃣ "
                        f"Consult our AI Medical Receptionist\n"
                    )

                    reply = (
                        "😔 No slots available for this doctor.\n\n"
                        "Please choose another specialization:\n\n"
                        f"{specialization_text}"
                    )

                else:
                    reply = build_date_list(
                        available_dates
                    )

    # =========================
    # HANDLE DATE SELECTION
    # =========================
    elif session and session.current_step == "selecting_date":

        available_dates = get_available_dates(
            db,
            session.selected_doctor_id
        )

        payload = effective_input

        if not payload.startswith("date_"):

            reply = "Invalid date selection."

        else:

            selected_index = int(
                payload.replace(
                    "date_",
                    ""
                )
            )

            if (
                selected_index < 0
                or selected_index >= len(available_dates)
            ):

                reply = "Invalid date selection."

            else:

                selected_date = available_dates[selected_index]

                session.selected_date = selected_date
                session.current_step = "selecting_session"

                db.commit()

                sessions = get_available_sessions_v2(
                    db,
                    session.selected_doctor_id,
                    selected_date
                )

                reply = build_session_list(
                    sessions
                )
                    
    # =========================
    # HANDLE SESSIONS SELECTION
    # =========================

    elif session and session.current_step == "selecting_session":

        sessions = get_available_sessions_v2(
            db,
            session.selected_doctor_id,
            session.selected_date
        )

        payload = effective_input

        if not payload.startswith("session_"):

            reply = "Invalid session selection."

        else:

            selected_index = int(
                payload.replace(
                    "session_",
                    ""
                )
            )

            if (
                selected_index < 0
                or selected_index >= len(sessions)
            ):

                reply = "Invalid session selection."

            else:

                session.selected_session = selected_index
                session.current_step = "selecting_slot"

                db.commit()

                slots = get_slots_for_selected_session(
                    db,
                    session.selected_doctor_id,
                    session.selected_date,
                    selected_index
                )

                reply = build_slot_list_page(
                    slots,
                    page=0
                )
    # =========================
    # HANDLE SLOT SELECTION
    # =========================
    elif session and session.current_step == "selecting_slot":

        slots = get_slots_for_selected_session(
            db,
            session.selected_doctor_id,
            session.selected_date,
            session.selected_session
        )

        payload = effective_input

        if payload.startswith("slot_page_"):

            page = int(
                payload.replace(
                    "slot_page_",
                    ""
                )
            )

            reply = build_slot_list_page(
                slots,
                page=page
            )

        elif payload.startswith("slot_"):

            slot_id = int(
                payload.replace(
                    "slot_",
                    ""
                )
            )

            selected_slot = next(
                (
                    slot
                    for slot in slots
                    if slot.id == slot_id
                ),
                None
            )

            if not selected_slot:

                reply = "Invalid slot selection."

            elif selected_slot.status != "available":

                reply = (
                    "Sorry, this slot was just booked.\n\n"
                    "Please go back and choose another slot."
                )

            else:

                selected_slot.status = "booked"

                user = db.query(User).filter(
                    User.phone_number == user_number
                ).first()

                appointment = Appointment(
                    user_id=user.id,
                    doctor_id=session.selected_doctor_id,
                    slot_id=selected_slot.id,
                    appointment_date=selected_slot.slot_date,
                    status="booked"
                )

                db.add(appointment)

                session.current_step = "idle"
                session.selected_specialization = None
                session.selected_doctor_id = None
                session.selected_date = None
                session.selected_session = None

                db.commit()

                doctor = db.query(Doctor).filter(
                    Doctor.id == appointment.doctor_id
                ).first()

                formatted_date = selected_slot.slot_date.strftime(
                    "%d %B %Y"
                )

                start_time = selected_slot.start_time.strftime(
                    "%I:%M %p"
                )

                reply = (
                    f"✅ Appointment booked!\n\n"
                    f"👨‍⚕️ Doctor: {doctor.name}\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {start_time}\n\n"
                    f"Thank you!"
                )

        else:

            reply = "Invalid slot selection."
    # =========================
    # HANDLE CANCEL — SELECT APPOINTMENT
    # =========================
    elif (
        session and
        session.current_step == "selecting_cancel"
    ):

        appointments = get_upcoming_appointments(
            user_number, db
        )

        if not normalized_msg.isdigit():

            reply = "Please enter a valid appointment number."

        else:

            selected_index = int(normalized_msg) - 1

            if (
                selected_index < 0
                or selected_index >= len(appointments)
            ):

                reply = "Invalid selection. Please try again."

            else:

                selected_appt = appointments[selected_index]

                # store appointment id in slot_id field temporarily
                session.selected_slot_id = selected_appt["id"]
                session.current_step     = "confirming_cancel"
                db.commit()

                reply = (
                    f"Are you sure you want to cancel?\n\n"
                    f"👨‍⚕️ {selected_appt['doctor_name']}\n"
                    f"📅 {selected_appt['date']} "
                    f"at {selected_appt['time']}\n\n"
                    f"1️⃣ Yes, cancel it\n"
                    f"2️⃣ No, keep it"
                )

    # =========================
    # HANDLE CANCEL — CONFIRM
    # =========================
    elif (
        session and
        session.current_step == "confirming_cancel"
    ):

        if normalized_msg == "1":

            appointment = db.query(Appointment).filter(
                Appointment.id == session.selected_slot_id
            ).first()

            if not appointment:

                reply = (
                    "⚠️ Appointment not found.\n\n"
                    "Reply *hi* to go back to the menu."
                )

            else:

                # free up the slot
                slot = db.query(DoctorSlot).filter(
                    DoctorSlot.id == appointment.slot_id
                ).first()

                if slot:
                    slot.status = "available"

                appointment.status = "cancelled"

                session.current_step     = "idle"
                session.selected_slot_id = None

                db.commit()

                reply = (
                    "✅ Appointment cancelled successfully.\n\n"
                    "Your slot has been freed up.\n\n"
                    "Reply *hi* to go back to the menu."
                )

        elif normalized_msg == "2":

            session.current_step     = "idle"
            session.selected_slot_id = None
            db.commit()

            reply = (
                "👍 No problem! Your appointment is kept.\n\n"
                "Reply *hi* to go back to the menu."
            )

        else:

            reply = (
                "Please reply with:\n\n"
                "1️⃣ Yes, cancel it\n"
                "2️⃣ No, keep it"
            )

    # =========================
    # MAIN MENU
    # =========================
    elif normalized_msg in [
        "hi", "hello", "hey", "menu", "hie"
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

        if not user:

            session.current_step = "collecting_name"
            db.commit()

            reply = (
                "👋 Welcome to City Clinic!\n\n"
                "Let's get you registered first.\n\n"
                "Please enter your full name."
            )

        else:

            specializations = get_specializations(db)
            session.current_step = "selecting_specialization"
            db.commit()

            reply = build_specialization_list(
                specializations,
                user.name
            )

    # =========================
    # CANCEL APPOINTMENT
    # =========================
    elif normalized_msg == "2":

        user = db.query(User).filter(
            User.phone_number == user_number
        ).first()

        if not user:

            reply = (
                "⚠️ You are not registered yet.\n\n"
                "Reply *1* to book your first appointment."
            )

        else:

            appointments = get_upcoming_appointments(
                user_number, db
            )

            if not appointments:

                reply = (
                    "📭 You have no upcoming appointments.\n\n"
                    "Reply *1* to book an appointment."
                )

            else:

                if not session:
                    session = UserSession(
                        phone_number=user_number,
                        current_step="idle"
                    )
                    db.add(session)
                    db.commit()
                    db.refresh(session)

                session.current_step = "selecting_cancel"
                db.commit()

                appt_text = format_appointments(appointments)

                reply = (
                    f"Your upcoming appointments:\n\n"
                    f"{appt_text}"
                    f"Which one would you like to cancel?\n"
                    f"Reply with the number."
                )

    # =========================
    # MY APPOINTMENTS
    # =========================
    elif normalized_msg == "3":

        user = db.query(User).filter(
            User.phone_number == user_number
        ).first()

        if not user:

            reply = (
                "⚠️ You are not registered yet.\n\n"
                "Reply *1* to book your first appointment."
            )

        else:

            appointments = get_upcoming_appointments(
                user_number, db
            )

            if not appointments:

                reply = (
                    "📭 You have no upcoming appointments.\n\n"
                    "Reply *1* to book an appointment."
                )

            else:

                appt_text = format_appointments(appointments)

                reply = (
                    f"📋 Your upcoming appointments:\n\n"
                    f"{appt_text}"
                    f"Reply *hi* to go back to the menu."
                )

    # =========================
    # CLINIC HOURS
    # =========================
    elif normalized_msg == "4":

        reply = (
            "🕐 We're open Mon–Sat, "
            "9 AM to 7 PM.\n"
            "Sunday: 10 AM to 2 PM."
        )

    # =========================
    # LOCATION
    # =========================
    elif normalized_msg == "5":

        reply = (
            "📍 123 Health Street, "
            "Near Central Park.\n"
            "Google Maps: "
            "https://maps.google.com/?q=..."
        )

    return reply


