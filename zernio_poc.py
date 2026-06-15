import os
import json
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY")


@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    payload = await request.json()

    print("\n" + "=" * 80)
    print("RAW PAYLOAD")
    print(json.dumps(payload, indent=2))
    print("=" * 80 + "\n")

    if payload.get("event") != "message.received":
        return JSONResponse(
            content={"status": "ignored"},
            status_code=status.HTTP_200_OK
        )

    message = payload.get("message", {})
    account = payload.get("account", {})

    conversation_id = message.get("conversationId")
    account_id = account.get("id")

    message_body = message.get("text", "").strip().lower()

    print(f"Message Body : {message_body}")
    print(f"Conversation : {conversation_id}")
    print(f"Account ID   : {account_id}")

    # --------------------------------------------------
    # Send list picker on HI
    # --------------------------------------------------
    if message_body == "hi":



        body = {
            "accountId": account_id,
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
                                    "id": "slot_0900",
                                    "title": "09:00 AM"
                                },
                                {
                                    "id": "slot_0915",
                                    "title": "09:15 AM"
                                },
                                {
                                    "id": "slot_0930",
                                    "title": "09:30 AM"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        r = requests.post(
            f"https://zernio.com/api/v1/inbox/conversations/{conversation_id}/messages",
            headers={
                "Authorization": f"Bearer {ZERNIO_API_KEY}",
                "Content-Type": "application/json"
            },
            json=body
        )

        print(
            f"Reply status: {r.status_code}\n"
            f"Response: {r.text}"
        )

    return JSONResponse(
        content={"status": "processed"},
        status_code=status.HTTP_200_OK
    )


@app.get("/")
def root():
    return {
        "status": "running"
    }