from config import client, FROM_NUMBER, TEST_MODE


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