import requests

r = requests.post(
    "https://clinic-booking-chatbot.onrender.com/webhook/zernio",
    json={"event": "test"}
)
print(r.status_code, r.text)