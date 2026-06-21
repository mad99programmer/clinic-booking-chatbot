from config import client, FROM_NUMBER, TEST_MODE, ZERNIO_API_KEY
import requests
from helpers import paginate_slots,has_next_page,has_previous_page
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
# SEND WHATSAPP MESSAGE using TWILIO
# =========================
def send_reply_twilio(to: str, message: str):

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
# SEND WHATSAPP MESSAGE using ZERNIO
# =========================

def send_reply(
    conversation_id: str,
    account_id: str,
    message
):
    if TEST_MODE:

        print("\nBOT REPLY:")
        print(message)
        return

    if isinstance(message, str):

        body = {
            "accountId": account_id,
            "message": message
        }

    else:

        body = {
            "accountId": account_id
        }

        if "message" in message:
            body["message"] = message["message"]

        if "buttons" in message:
            body["buttons"] = message["buttons"]

        if "interactive" in message:
            body["interactive"] = message["interactive"]

    print("OUTGOING BODY:")
    print(body)

    r = requests.post(
        f"https://zernio.com/api/v1/inbox/conversations/{conversation_id}/messages",
        headers={
            "Authorization": f"Bearer {ZERNIO_API_KEY}",
            "Content-Type": "application/json"
        },
        json=body
    )

    print(
        f"Reply status: {r.status_code}, "
        f"Response: {r.text}"
    )


#Below function is responsible for creating list picker for specialization (physician,cardiologist etc)
def build_specialization_list(
    specializations,
    user_name
):
    rows = []

    for index, specialization in enumerate(
        specializations
    ):

        rows.append(
            {
                "id": f"specialization_{index}",
                "title": specialization
            }
        )

    rows.append(
        {
            "id": "ai_receptionist",
            "title": "Consult our AI"
        }
    )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": (
                    f"Welcome back {user_name} 👋\n\n"
                    f"Choose a specialization:"
                )
            },
            "action": {
                "button": "Select",
                "sections": [
                    {
                        "title": "Options",
                        "rows": rows
                    }
                ]
            }
        }
    }


#Below function is responsible for creating list picker for doctors (Dr Manta, Dr Pinkesh....)
def build_doctor_list(doctors):

    rows = []

    for doctor in doctors:

        rows.append(
            {
                "id": f"doctor_{doctor.id}",
                "title": doctor.name
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please select a doctor:"
            },
            "action": {
                "button": "Select Doctor",
                "sections": [
                    {
                        "title": "Available Doctors",
                        "rows": rows
                    }
                ]
            }
        }
    }

#Below function is responsible for creating list picker for dates
def build_date_list(
    available_dates
):

    rows = []

    for index, slot_date in enumerate(
        available_dates
    ):

        formatted_date = slot_date.strftime(
            "%d %B %Y"
        )

        rows.append(
            {
                "id": f"date_{index}",
                "title": formatted_date
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please select a date:"
            },
            "action": {
                "button": "Select Date",
                "sections": [
                    {
                        "title": "Available Dates",
                        "rows": rows
                    }
                ]
            }
        }
    }

def build_session_list(
    sessions
):

    rows = []

    for index, session in enumerate(
        sessions
    ):

        start_time = session["start"].strftime(
            "%I:%M %p"
        )

        end_time = session["end"].strftime(
            "%I:%M %p"
        )

        rows.append(
            {
                "id": f"session_{index}",
                "title": (
                    f"{start_time} - "
                    f"{end_time}"
                )
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please select a session:"
            },
            "action": {
                "button": "Select Session",
                "sections": [
                    {
                        "title": "Available Sessions",
                        "rows": rows
                    }
                ]
            }
        }
    }


#Below function is responsible for creating list picker for slots (9:00 am,9:15 am .....)
def build_slot_list_page(slots,page=0):
    page_slots = paginate_slots(
    slots,
    page
)
    rows = []
    for slot in page_slots:

        rows.append(
            {
                "id": f"slot_{slot.id}",
                "title": slot.start_time.strftime(
                    "%I:%M %p"
                )
            }
        )
    if has_previous_page(page):

        rows.append(
            {
                "id": f"slot_page_{page - 1}",
                "title": "⬅ Previous Slots"
            }
        )
    if has_next_page(slots,page):
        rows.append(
            {
                "id": f"slot_page_{page + 1}",
                "title": "➡ More Slots"
            }
        )
    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Choose an available slot:"
            },
            "action": {
                "button": "Select Slot",
                "sections": [
                    {
                        "title": "Available Slots",
                        "rows": rows
                    }
                ]
            }
        }
    }