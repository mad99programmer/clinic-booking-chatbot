# =========================
# handlers.py  â€“  City Clinic WhatsApp Bot
# Zernio interactive-message edition
# =========================

from __future__ import annotations

from datetime import date
from typing import Any

from ai_receptionist import suggest_specialization
from crud import (
    get_available_dates,
    get_available_sessions,
    get_available_slots,
    get_doctors_by_specialization,
    get_specializations,
)
from models import Appointment, Doctor, DoctorSlot, User, UserSession
from validators import is_valid_age, is_valid_email, is_valid_name

# ---------------------------------------------------------------------------
# PAYLOAD CONSTANTS
# ---------------------------------------------------------------------------

P_BOOK_APPOINTMENT   = "book_appointment"
P_CANCEL_APPOINTMENT = "cancel_appointment"
P_MY_APPOINTMENTS    = "my_appointments"
P_CLINIC_HOURS       = "clinic_hours"
P_LOCATION           = "location"

P_CONFIRM_REGISTRATION = "confirm_registration"
P_RESTART_REGISTRATION = "restart_registration"

P_AI_RECEPTIONIST    = "ai_receptionist"
P_CONFIRM_BOOKING    = "confirm_booking"
P_CANCEL_BOOKING     = "cancel_booking"

P_CONFIRM_CANCEL     = "confirm_cancel"
P_KEEP_APPOINTMENT   = "keep_appointment"

PREFIX_SPECIALIZATION = "specialization_"
PREFIX_DOCTOR         = "doctor_"
PREFIX_DATE           = "date_"
PREFIX_SESSION        = "session_"
PREFIX_SLOT           = "slot_"
PREFIX_CANCEL_APPT    = "cancel_appt_"

MENU_RESET_KEYWORDS = {"hi", "hello", "hey", "menu", "home", "reset", "hie"}

MAX_LIST_ROWS = 10   # Zernio list section row limit


# ---------------------------------------------------------------------------
# PAYLOAD EXTRACTOR
# ---------------------------------------------------------------------------

def extract_payload(webhook_data: dict[str, Any] | None) -> str:
    """
    Safely extract the interactive payload from a Zernio webhook message dict.

    Priority:
      1. button_reply.id
      2. list_reply.id
      3. text body (fallback for free-text steps)

    Pass the inner ``message`` object from the webhook payload.
    If webhook_data is None or missing fields, returns "".
    """
    if not webhook_data:
        return ""

    raw = webhook_data.get("raw", {}) or {}
    interactive = raw.get("interactive", {}) or {}

    button_reply = interactive.get("button_reply", {}) or {}
    if button_reply.get("id"):
        return button_reply["id"].strip()

    list_reply = interactive.get("list_reply", {}) or {}
    if list_reply.get("id"):
        return list_reply["id"].strip()

    # Fallback: plain text
    return webhook_data.get("text", "").strip()


# ---------------------------------------------------------------------------
# INTERACTIVE MESSAGE BUILDERS
# Zernio send_reply signature: send_reply(conversation_id, account_id, message)
# For interactive content we return a dict; callers must handle both str and dict.
# ---------------------------------------------------------------------------

def build_main_menu() -> dict:
    return {
        "message": "ðŸ‘‹ Welcome to City Clinic!\n\nHow can we help you today?",
        "buttons": [
            {"title": "ðŸ“… Book Appointment",  "payload": P_BOOK_APPOINTMENT},
            {"title": "âŒ Cancel Appointment", "payload": P_CANCEL_APPOINTMENT},
            {"title": "ðŸ“‹ More Options",       "payload": "more_options"},
        ],
    }


def build_more_options_menu() -> dict:
    return {
        "message": "Choose an option:",
        "buttons": [
            {"title": "ðŸ—“ My Appointments", "payload": P_MY_APPOINTMENTS},
            {"title": "ðŸ• Clinic Hours",    "payload": P_CLINIC_HOURS},
            {"title": "ðŸ“ Location",        "payload": P_LOCATION},
        ],
    }


def build_gender_buttons() -> dict:
    return {
        "message": "Please select your gender:",
        "buttons": [
            {"title": "Male",             "payload": "gender_male"},
            {"title": "Female",           "payload": "gender_female"},
            {"title": "Prefer not to say","payload": "gender_other"},
        ],
    }


def build_confirm_registration_buttons(session: UserSession) -> dict:
    return {
        "message": (
            f"Please confirm your details:\n\n"
            f"ðŸ‘¤ Name: {session.temp_name}\n"
            f"ðŸ“§ Email: {session.temp_email}\n"
            f"âš§ Gender: {session.temp_gender}\n"
            f"ðŸŽ‚ Age: {session.temp_age}"
        ),
        "buttons": [
            {"title": "âœ… Confirm",     "payload": P_CONFIRM_REGISTRATION},
            {"title": "ðŸ”„ Start Over", "payload": P_RESTART_REGISTRATION},
        ],
    }


def build_specialization_list(
    specializations: list[str],
    recommended: str | None = None,
) -> dict:
    rows = []
    for spec in specializations:
        label = f"â­ {spec} (Recommended)" if spec == recommended else spec
        rows.append({
            "id":          f"{PREFIX_SPECIALIZATION}{spec}",
            "title":       label[:24],          # Zernio title limit
            "description": spec if spec == recommended else "",
        })
    rows.append({
        "id":    P_AI_RECEPTIONIST,
        "title": "ðŸ¤– AI Receptionist",
        "description": "Describe symptoms, get a recommendation",
    })
    return {
        "message": "ðŸ¥ Choose a specialization:",
        "interactive": {
            "type": "list",
            "action": {
                "button": "View Specializations",
                "sections": [{"title": "Specializations", "rows": rows}],
            },
        },
    }


def build_doctor_list(doctors: list[Doctor], specialization: str) -> dict:
    rows = [
        {
            "id":          f"{PREFIX_DOCTOR}{d.id}",
            "title":       d.name[:24],
            "description": getattr(d, "qualification", "") or "",
        }
        for d in doctors
    ]
    return {
        "message": f"ðŸ‘¨â€âš•ï¸ Available doctors for *{specialization}*:",
        "interactive": {
            "type": "list",
            "action": {
                "button": "Choose Doctor",
                "sections": [{"title": "Doctors", "rows": rows}],
            },
        },
    }


def build_date_list(available_dates: list, doctor_name: str) -> dict:
    rows = [
        {
            "id":    f"{PREFIX_DATE}{d.strftime('%Y_%m_%d')}",
            "title": d.strftime("%d %B %Y"),
        }
        for d in available_dates[:MAX_LIST_ROWS]
    ]
    return {
        "message": f"ðŸ“… Available dates for *{doctor_name}*:",
        "interactive": {
            "type": "list",
            "action": {
                "button": "Pick a Date",
                "sections": [{"title": "Dates", "rows": rows}],
            },
        },
    }


def build_session_list(sessions: list[dict], selected_date: date) -> dict:
    rows = []
    for idx, s in enumerate(sessions):
        start = s["start"].strftime("%I:%M %p")
        end   = s["end"].strftime("%I:%M %p")
        rows.append({
            "id":    f"{PREFIX_SESSION}{idx}",
            "title": f"{start} â€“ {end}",
        })
    return {
        "message": (
            f"ðŸ“… *{selected_date.strftime('%d %B %Y')}*\n\n"
            "Choose a session:"
        ),
        "interactive": {
            "type": "list",
            "action": {
                "button": "Choose Session",
                "sections": [{"title": "Sessions", "rows": rows}],
            },
        },
    }


def build_slot_list(slots: list[DoctorSlot]) -> dict:
    rows = [
        {
            "id":    f"{PREFIX_SLOT}{s.id}",
            "title": (
                f"{s.start_time.strftime('%I:%M %p')} â€“ "
                f"{s.end_time.strftime('%I:%M %p')}"
            ),
        }
        for s in slots[:MAX_LIST_ROWS]
    ]
    return {
        "message": "â° Choose an available slot:",
        "interactive": {
            "type": "list",
            "action": {
                "button": "Pick a Slot",
                "sections": [{"title": "Slots", "rows": rows}],
            },
        },
    }


def build_confirm_booking_buttons(
    doctor_name: str,
    appt_date: str,
    slot_time: str,
) -> dict:
    return {
        "message": (
            f"Please confirm your appointment:\n\n"
            f"ðŸ‘¨â€âš•ï¸ Doctor: {doctor_name}\n"
            f"ðŸ“… Date: {appt_date}\n"
            f"â° Time: {slot_time}"
        ),
        "buttons": [
            {"title": "âœ… Confirm", "payload": P_CONFIRM_BOOKING},
            {"title": "âŒ Cancel",  "payload": P_CANCEL_BOOKING},
        ],
    }


def build_cancel_list(appointments: list[dict]) -> dict:
    rows = [
        {
            "id":    f"{PREFIX_CANCEL_APPT}{a['id']}",
            "title": a["doctor_name"][:24],
            "description": f"{a['date']} at {a['time']}",
        }
        for a in appointments[:MAX_LIST_ROWS]
    ]
    return {
        "message": "Your upcoming appointments.\n\nSelect one to cancel:",
        "interactive": {
            "type": "list",
            "action": {
                "button": "Choose Appointment",
                "sections": [{"title": "Appointments", "rows": rows}],
            },
        },
    }


def build_confirm_cancel_buttons(appt: dict) -> dict:
    return {
        "message": (
            f"Are you sure you want to cancel?\n\n"
            f"ðŸ‘¨â€âš•ï¸ {appt['doctor_name']}\n"
            f"ðŸ“… {appt['date']} at {appt['time']}"
        ),
        "buttons": [
            {"title": "âœ… Yes, Cancel",    "payload": P_CONFIRM_CANCEL},
            {"title": "ðŸ”™ No, Keep It",    "payload": P_KEEP_APPOINTMENT},
        ],
    }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

GENDER_PAYLOAD_MAP = {
    "gender_male":   "Male",
    "gender_female": "Female",
    "gender_other":  "Prefer not to say",
}


def _reset_session(session: UserSession, db) -> None:
    session.current_step            = "idle"
    session.temp_name               = None
    session.temp_email              = None
    session.temp_gender             = None
    session.temp_age                = None
    session.selected_specialization = None
    session.selected_doctor_id      = None
    session.selected_slot_id        = None
    session.selected_date           = None
    session.selected_session        = None
    db.commit()


def _ensure_session(user_number: str, db) -> UserSession:
    session = db.query(UserSession).filter(
        UserSession.phone_number == user_number
    ).first()
    if not session:
        session = UserSession(phone_number=user_number, current_step="idle")
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_upcoming_appointments(user_number: str, db) -> list[dict]:
    user = db.query(User).filter(User.phone_number == user_number).first()
    if not user:
        return []

    today = date.today()
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.user_id == user.id,
            Appointment.status == "booked",
            Appointment.appointment_date >= today,
        )
        .order_by(Appointment.appointment_date)
        .all()
    )

    result = []
    for appt in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        slot   = db.query(DoctorSlot).filter(DoctorSlot.id == appt.slot_id).first()
        result.append({
            "id":          appt.id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "date":        appt.appointment_date.strftime("%d %B %Y"),
            "time":        slot.start_time.strftime("%I:%M %p") if slot else "",
            "slot_id":     appt.slot_id,
        })
    return result


def _format_appointments_text(appointments: list[dict]) -> str:
    lines = []
    for appt in appointments:
        lines.append(
            f"ðŸ‘¨â€âš•ï¸ {appt['doctor_name']}\n"
            f"   ðŸ“… {appt['date']} at {appt['time']}"
        )
    return "\n\n".join(lines)


def _get_session_filtered_slots(
    db,
    doctor_id: int,
    selected_date: date,
    session_index: int,
) -> list[DoctorSlot]:
    sessions = get_available_sessions(db, doctor_id, selected_date)
    if session_index < 0 or session_index >= len(sessions):
        return []
    chosen_session = sessions[session_index]
    all_slots = get_available_slots(db, doctor_id, selected_date)
    return [
        s for s in all_slots
        if s.start_time >= chosen_session["start"]
        and s.end_time <= chosen_session["end"]
    ]


def _specialization_list_response(
    db, recommended: str | None = None
) -> dict:
    specs = get_specializations(db)
    return build_specialization_list(specs, recommended=recommended)


# ---------------------------------------------------------------------------
# FLOW HANDLERS  (one function per step)
# ---------------------------------------------------------------------------

def _handle_collecting_name(session, payload, raw_text, db) -> str | dict:
    if not is_valid_name(raw_text):
        return (
            "âš ï¸ That doesn't look like a valid name.\n\n"
            "Please enter your full name.\n"
            "Example: *John Doe*"
        )
    session.temp_name    = raw_text.strip()
    session.current_step = "collecting_email"
    db.commit()
    return (
        f"âœ… Got it, *{session.temp_name}*!\n\n"
        "Please enter your email address."
    )


def _handle_collecting_email(session, payload, raw_text, db) -> str | dict:
    if not is_valid_email(raw_text):
        return (
            "âš ï¸ Invalid email address.\n\n"
            "Example: john@example.com"
        )
    session.temp_email   = raw_text.strip().lower()
    session.current_step = "collecting_gender"
    db.commit()
    return build_gender_buttons()


def _handle_collecting_gender(session, payload, db) -> str | dict:
    gender = GENDER_PAYLOAD_MAP.get(payload)
    if not gender:
        return build_gender_buttons()
    session.temp_gender  = gender
    session.current_step = "collecting_age"
    db.commit()
    return "Please enter your age.\n\nExample: *25*"


def _handle_collecting_age(session, payload, raw_text, db) -> str | dict:
    if not is_valid_age(raw_text):
        return "âš ï¸ Please enter a valid age.\n\nExample: *25*"
    session.temp_age     = int(raw_text.strip())
    session.current_step = "confirming_details"
    db.commit()
    return build_confirm_registration_buttons(session)


def _handle_confirming_details(
    session, payload, user_number: str, db
) -> str | dict:
    if payload == P_CONFIRM_REGISTRATION:
        new_user = User(
            phone_number=user_number,
            name=session.temp_name,
            email=session.temp_email,
            gender=session.temp_gender,
            age=session.temp_age,
        )
        db.add(new_user)
        session.temp_name            = None
        session.temp_email           = None
        session.temp_gender          = None
        session.temp_age             = None
        session.current_step         = "selecting_specialization"
        db.commit()
        db.refresh(new_user)
        return _specialization_list_response(db)

    if payload == P_RESTART_REGISTRATION:
        session.temp_name            = None
        session.temp_email           = None
        session.temp_gender          = None
        session.temp_age             = None
        session.current_step         = "collecting_name"
        db.commit()
        return "No problem!\n\nPlease enter your full name."

    return build_confirm_registration_buttons(session)


def _handle_selecting_specialization(
    session, payload, db
) -> str | dict:
    if payload == P_AI_RECEPTIONIST:
        session.current_step = "ai_symptom_collection"
        db.commit()
        return "ðŸ¤– Please describe your symptoms and we'll suggest a specialization."

    if payload.startswith(PREFIX_SPECIALIZATION):
        specialization = payload[len(PREFIX_SPECIALIZATION):]
        specs = get_specializations(db)
        if specialization not in specs:
            return _specialization_list_response(db)

        session.selected_specialization = specialization
        session.current_step            = "selecting_doctor"
        db.commit()

        doctors = get_doctors_by_specialization(db, specialization)
        if not doctors:
            session.current_step = "selecting_specialization"
            db.commit()
            return (
                "ðŸ˜” No doctors available for that specialization.\n\n"
                + _specialization_list_response(db)["message"]
            )
        return build_doctor_list(doctors, specialization)

    return _specialization_list_response(db)


def _handle_ai_symptom_collection(
    session, raw_text: str, db
) -> str | dict:
    specializations = get_specializations(db)
    ai_result       = suggest_specialization(raw_text, specializations)
    recommended     = ai_result.get("assigned_specialization")

    session.current_step = "selecting_specialization"
    db.commit()

    response = _specialization_list_response(db, recommended=recommended)
    response["message"] = (
        f"ðŸ¤– Based on your symptoms, we recommend:\n\n"
        f"ðŸ¥ *{recommended}*\n\n"
        "You can still choose any specialization below:"
    )
    return response


def _handle_selecting_doctor(session, payload, db) -> str | dict:
    if not payload.startswith(PREFIX_DOCTOR):
        doctors = get_doctors_by_specialization(
            db, session.selected_specialization
        )
        return build_doctor_list(doctors, session.selected_specialization)

    doctor_id = int(payload[len(PREFIX_DOCTOR):])
    doctor    = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return "âš ï¸ Doctor not found. Please try again."

    session.selected_doctor_id = doctor_id
    session.current_step       = "selecting_date"
    db.commit()

    available_dates = get_available_dates(db, doctor_id)
    if not available_dates:
        session.current_step       = "selecting_specialization"
        session.selected_doctor_id = None
        db.commit()
        response = _specialization_list_response(db)
        response["message"] = (
            "ðŸ˜” No slots available for this doctor.\n\n"
            "Please choose another specialization:"
        )
        return response

    return build_date_list(available_dates, doctor.name)


def _handle_selecting_date(session, payload, db) -> str | dict:
    if not payload.startswith(PREFIX_DATE):
        available_dates = get_available_dates(db, session.selected_doctor_id)
        doctor = db.query(Doctor).filter(
            Doctor.id == session.selected_doctor_id
        ).first()
        return build_date_list(available_dates, doctor.name if doctor else "")

    date_str      = payload[len(PREFIX_DATE):]      # e.g. "2026_06_15"
    selected_date = date(*[int(p) for p in date_str.split("_")])

    session.selected_date = selected_date
    session.current_step  = "selecting_session"
    db.commit()

    sessions = get_available_sessions(db, session.selected_doctor_id, selected_date)
    if not sessions:
        return (
            f"ðŸ˜” No sessions available for "
            f"{selected_date.strftime('%d %B %Y')}.\n\n"
            "Please pick another date."
        )
    return build_session_list(sessions, selected_date)


def _handle_selecting_session(session, payload, db) -> str | dict:
    if not payload.startswith(PREFIX_SESSION):
        sessions = get_available_sessions(
            db, session.selected_doctor_id, session.selected_date
        )
        return build_session_list(sessions, session.selected_date)

    session_index = int(payload[len(PREFIX_SESSION):])
    slots = _get_session_filtered_slots(
        db, session.selected_doctor_id, session.selected_date, session_index
    )

    if not slots:
        return (
            "ðŸ˜” No slots available for this session.\n\n"
            "Please choose another session."
        )

    session.selected_session = session_index
    session.current_step     = "selecting_slot"
    db.commit()

    return build_slot_list(slots)


def _handle_selecting_slot(session, payload, user_number: str, db) -> str | dict:
    if not payload.startswith(PREFIX_SLOT):
        slots = _get_session_filtered_slots(
            db,
            session.selected_doctor_id,
            session.selected_date,
            session.selected_session,
        )
        return build_slot_list(slots)

    slot_id       = int(payload[len(PREFIX_SLOT):])
    selected_slot = db.query(DoctorSlot).filter(DoctorSlot.id == slot_id).first()

    if not selected_slot or selected_slot.status != "available":
        return (
            "âš ï¸ Sorry, this slot was just booked by someone else.\n\n"
            "Please choose another slot."
        )

    # Temporarily hold the chosen slot in session for the confirm step
    session.selected_slot_id = slot_id
    session.current_step     = "confirming_booking"
    db.commit()

    doctor = db.query(Doctor).filter(
        Doctor.id == session.selected_doctor_id
    ).first()

    return build_confirm_booking_buttons(
        doctor_name=doctor.name if doctor else "Unknown",
        appt_date=selected_slot.slot_date.strftime("%d %B %Y"),
        slot_time=selected_slot.start_time.strftime("%I:%M %p"),
    )


def _handle_confirming_booking(
    session, payload, user_number: str, db
) -> str | dict:
    if payload == P_CANCEL_BOOKING:
        _reset_session(session, db)
        return build_main_menu()

    if payload != P_CONFIRM_BOOKING:
        # Re-show confirm buttons (edge case: unexpected payload)
        slot = db.query(DoctorSlot).filter(
            DoctorSlot.id == session.selected_slot_id
        ).first()
        doctor = db.query(Doctor).filter(
            Doctor.id == session.selected_doctor_id
        ).first()
        return build_confirm_booking_buttons(
            doctor_name=doctor.name if doctor else "Unknown",
            appt_date=slot.slot_date.strftime("%d %B %Y") if slot else "",
            slot_time=slot.start_time.strftime("%I:%M %p") if slot else "",
        )

    # Re-check availability
    selected_slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == session.selected_slot_id
    ).first()

    if not selected_slot or selected_slot.status != "available":
        session.current_step     = "selecting_slot"
        session.selected_slot_id = None
        db.commit()
        slots = _get_session_filtered_slots(
            db,
            session.selected_doctor_id,
            session.selected_date,
            session.selected_session,
        )
        return (
            "âš ï¸ That slot was just taken. Please choose another:"
            if not slots
            else build_slot_list(slots)
        )

    selected_slot.status = "booked"

    user = db.query(User).filter(User.phone_number == user_number).first()
    appointment = Appointment(
        user_id=user.id,
        doctor_id=session.selected_doctor_id,
        slot_id=selected_slot.id,
        appointment_date=selected_slot.slot_date,
        status="booked",
    )
    db.add(appointment)

    doctor = db.query(Doctor).filter(
        Doctor.id == session.selected_doctor_id
    ).first()
    formatted_date = selected_slot.slot_date.strftime("%d %B %Y")
    start_time     = selected_slot.start_time.strftime("%I:%M %p")

    _reset_session(session, db)

    return (
        f"âœ… *Appointment Confirmed!*\n\n"
        f"ðŸ‘¨â€âš•ï¸ Doctor: {doctor.name if doctor else 'Unknown'}\n"
        f"ðŸ“… Date: {formatted_date}\n"
        f"â° Time: {start_time}\n\n"
        f"Thank you for choosing City Clinic! ðŸ¥\n\n"
        f"Reply *hi* to return to the menu."
    )


def _handle_selecting_cancel(session, payload, user_number: str, db) -> str | dict:
    if not payload.startswith(PREFIX_CANCEL_APPT):
        appointments = get_upcoming_appointments(user_number, db)
        return build_cancel_list(appointments)

    appt_id = int(payload[len(PREFIX_CANCEL_APPT):])
    appointments = get_upcoming_appointments(user_number, db)
    selected = next((a for a in appointments if a["id"] == appt_id), None)

    if not selected:
        return "âš ï¸ Appointment not found. Please try again."

    # Reuse selected_slot_id field to temporarily store appointment id
    session.selected_slot_id = appt_id
    session.current_step     = "confirming_cancel"
    db.commit()

    return build_confirm_cancel_buttons(selected)


def _handle_confirming_cancel(
    session, payload, user_number: str, db
) -> str | dict:
    if payload == P_KEEP_APPOINTMENT:
        _reset_session(session, db)
        return "ðŸ‘ No problem! Your appointment is kept.\n\nReply *hi* to return to the menu."

    if payload != P_CONFIRM_CANCEL:
        # Re-fetch the appointment details for the confirm buttons
        appointments = get_upcoming_appointments(user_number, db)
        selected = next(
            (a for a in appointments if a["id"] == session.selected_slot_id), None
        )
        return (
            build_confirm_cancel_buttons(selected)
            if selected
            else build_main_menu()
        )

    appointment = db.query(Appointment).filter(
        Appointment.id == session.selected_slot_id
    ).first()

    if not appointment:
        _reset_session(session, db)
        return "âš ï¸ Appointment not found.\n\nReply *hi* to return to the menu."

    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == appointment.slot_id
    ).first()
    if slot:
        slot.status = "available"

    appointment.status = "cancelled"
    _reset_session(session, db)

    return (
        "âœ… Appointment cancelled successfully.\n\n"
        "Your slot has been freed up.\n\n"
        "Reply *hi* to return to the menu."
    )


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def process_message(
    user_number: str,
    incoming_msg: str,
    db,
    webhook_data: dict | None = None,
) -> str | dict:
    """
    Main message processor.

    Parameters
    ----------
    user_number   : Caller's phone number (E.164 without 'whatsapp:' prefix).
    incoming_msg  : Raw text from the message body (used for free-text steps).
    db            : SQLAlchemy Session.
    webhook_data  : The inner ``message`` object from the Zernio webhook payload.
                    When supplied, interactive button/list payloads are extracted
                    from it; otherwise ``incoming_msg`` is used as the payload.

    Returns
    -------
    str | dict    : A plain string for simple text replies, or a dict with
                    ``message`` + ``buttons`` / ``interactive`` keys for
                    Zernio interactive messages.  The caller (webhook handler)
                    is responsible for serialising the dict correctly when
                    calling send_reply().
    """

    payload      = extract_payload(webhook_data) if webhook_data else incoming_msg.strip()
    raw_text     = incoming_msg.strip()
    normalized   = raw_text.lower()
    session      = _ensure_session(user_number, db)

    # ------------------------------------------------------------------
    # GLOBAL RESET â€” any greeting keyword resets the flow
    # ------------------------------------------------------------------
    if normalized in MENU_RESET_KEYWORDS:
        _reset_session(session, db)
        return build_main_menu()

    # ------------------------------------------------------------------
    # REGISTRATION FLOW  (free-text steps come first)
    # ------------------------------------------------------------------
    if session.current_step == "collecting_name":
        return _handle_collecting_name(session, payload, raw_text, db)

    if session.current_step == "collecting_email":
        return _handle_collecting_email(session, payload, raw_text, db)

    if session.current_step == "collecting_gender":
        return _handle_collecting_gender(session, payload, db)

    if session.current_step == "collecting_age":
        return _handle_collecting_age(session, payload, raw_text, db)

    if session.current_step == "confirming_details":
        return _handle_confirming_details(session, payload, user_number, db)

    # ------------------------------------------------------------------
    # BOOKING FLOW
    # ------------------------------------------------------------------
    if session.current_step == "selecting_specialization":
        return _handle_selecting_specialization(session, payload, db)

    if session.current_step == "ai_symptom_collection":
        return _handle_ai_symptom_collection(session, raw_text, db)

    if session.current_step == "selecting_doctor":
        return _handle_selecting_doctor(session, payload, db)

    if session.current_step == "selecting_date":
        return _handle_selecting_date(session, payload, db)

    if session.current_step == "selecting_session":
        return _handle_selecting_session(session, payload, db)

    if session.current_step == "selecting_slot":
        return _handle_selecting_slot(session, payload, user_number, db)

    if session.current_step == "confirming_booking":
        return _handle_confirming_booking(session, payload, user_number, db)

    # ------------------------------------------------------------------
    # CANCELLATION FLOW
    # ------------------------------------------------------------------
    if session.current_step == "selecting_cancel":
        return _handle_selecting_cancel(session, payload, user_number, db)

    if session.current_step == "confirming_cancel":
        return _handle_confirming_cancel(session, payload, user_number, db)

    # ------------------------------------------------------------------
    # IDLE / MAIN MENU ACTIONS
    # ------------------------------------------------------------------

    if payload == P_BOOK_APPOINTMENT:
        user = db.query(User).filter(User.phone_number == user_number).first()
        if not user:
            session.current_step = "collecting_name"
            db.commit()
            return (
                "ðŸ‘‹ Welcome to City Clinic!\n\n"
                "Let's get you registered first.\n\n"
                "Please enter your full name."
            )
        session.current_step = "selecting_specialization"
        db.commit()
        specs = get_specializations(db)
        response = build_specialization_list(specs)
        response["message"] = f"Welcome back *{user.name}* ðŸ‘‹\n\n" + response["message"]
        return response

    if payload == P_CANCEL_APPOINTMENT:
        user = db.query(User).filter(User.phone_number == user_number).first()
        if not user:
            return (
                "âš ï¸ You are not registered yet.\n\n"
                "Tap *Book Appointment* to get started."
            )
        appointments = get_upcoming_appointments(user_number, db)
        if not appointments:
            return (
                "ðŸ“­ You have no upcoming appointments.\n\n"
                "Reply *hi* to return to the menu."
            )
        session.current_step = "selecting_cancel"
        db.commit()
        return build_cancel_list(appointments)

    if payload == P_MY_APPOINTMENTS:
        user = db.query(User).filter(User.phone_number == user_number).first()
        if not user:
            return (
                "âš ï¸ You are not registered yet.\n\n"
                "Tap *Book Appointment* to get started."
            )
        appointments = get_upcoming_appointments(user_number, db)
        if not appointments:
            return (
                "ðŸ“­ You have no upcoming appointments.\n\n"
                "Reply *hi* to return to the menu."
            )
        return (
            f"ðŸ“‹ *Your Upcoming Appointments*\n\n"
            f"{_format_appointments_text(appointments)}\n\n"
            f"Reply *hi* to return to the menu."
        )

    if payload == P_CLINIC_HOURS:
        return (
            "ðŸ• *Clinic Hours*\n\n"
            "Mon â€“ Sat: 9:00 AM â€“ 7:00 PM\n"
            "Sunday:    10:00 AM â€“ 2:00 PM"
        )

    if payload == P_LOCATION:
        return (
            "ðŸ“ *City Clinic*\n\n"
            "123 Health Street, Near Central Park.\n\n"
            "ðŸ—º Google Maps: https://maps.google.com/?q=..."
        )

    if payload == "more_options":
        return build_more_options_menu()

    # ------------------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------------------
    return build_main_menu()
