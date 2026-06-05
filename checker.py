import requests

r = requests.post(
    "https://zernio.com/api/v1/whatsapp/sandbox/messages",
    headers={
        "Authorization": "Bearer sk_6ea1cccfd3e83c142cc4dea49686339eaf28ddf75f1014d2eef73e792b317d1e",
        "Content-Type": "application/json"
    },
    json={
        "to": "+919833851621",
        "text": "test reply from bot"
    }
)
print(r.status_code)
print(r.text)