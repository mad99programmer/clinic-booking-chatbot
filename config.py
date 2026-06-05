import os
from twilio.rest import Client
from dotenv import load_dotenv
 
load_dotenv()
 
# =========================
# TWILIO CONFIG
# =========================
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
 
FROM_NUMBER = "whatsapp:+14155238886"
 
TEST_MODE = False
 
client = Client(ACCOUNT_SID, AUTH_TOKEN)


# =========================
# ZERNIO CONFIG
# =========================
ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY")