import requests

response = requests.post(
    "https://zernio.com/api/v1/whatsapp/sandbox/sessions",
    headers={
        "Authorization": "Bearer sk_6ea1cccfd3e83c142cc4dea49686339eaf28ddf75f1014d2eef73e792b317d1e",
        "Content-Type": "application/json"
    },
    json={"phone": "+919833851621"}  # your actual number
)
print(response.json())