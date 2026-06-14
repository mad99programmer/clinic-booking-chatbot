from config import client, FROM_NUMBER, TEST_MODE, ZERNIO_API_KEY
import requests

# =========================
# DISPLAY MENU
# =========================
def display_menu():
    return (
        "ðŸ‘‹ Welcome to City Clinic!\n\n"
        "Please choose an option:\n\n"
        "1ï¸âƒ£ Book Appointment\n"
        "2ï¸âƒ£ Cancel Appointment\n"
        "3ï¸âƒ£ My Appointments\n"
        "4ï¸âƒ£ Clinic Hours\n"
        "5ï¸âƒ£ Location"
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

def send_reply(conversation_id: str, account_id: str, message):
    """
    Send a reply via Zernio.

    ``message`` can be:
    - str  â†’ plain text message
    - dict â†’ interactive payload (buttons / list) produced by handlers.py
              Expected keys: "message" (str), and either "buttons" (list)
              or "interactive" (dict).
    """
    if TEST_MODE:
        print("\nBOT REPLY:")
        print(message)
        return

    if isinstance(message, str):
        body = {"accountId": account_id, "message": message}
    else:
        # Interactive dict from build_*() helpers
        body = {"accountId": account_id}
        body["message"] = message.get("message", "")
        if "buttons" in message:
            body["buttons"] = message["buttons"]
        if "interactive" in message:
            body["interactive"] = message["interactive"]

    r = requests.post(
        f"https://zernio.com/api/v1/inbox/conversations/{conversation_id}/messages",
        headers={
            "Authorization": f"Bearer {ZERNIO_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    print(f"Reply status: {r.status_code}, Response: {r.text}")