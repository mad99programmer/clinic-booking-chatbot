from config import client, FROM_NUMBER, TEST_MODE, ZERNIO_API_KEY
import requests

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

    
def build_slot_list_page(
    slots,
    page=0
):
    return {
        "message": "Choose an available slot:",
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
                        "rows": [
                            {
                                "id": "slot_1",
                                "title": "10:00 AM"
                            },
                            {
                                "id": "slot_2",
                                "title": "10:15 AM"
                            }
                        ]
                    }
                ]
            }
        }
    }