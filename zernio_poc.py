import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import requests

load_dotenv()  # loads the .env file

app = FastAPI()

ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY")

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    payload = await request.json()
    
    #print("RAW PAYLOAD:", payload)
    
    if payload.get("event") == "message.received":
        message = payload.get("message", {})
        account = payload.get("account", {})
        
        message_body = message.get("text", "").strip().lower()
        conversation_id = message.get("conversationId")
        account_id = account.get("id")
        
        print(f"Message: {message_body}, ConversationId: {conversation_id}, AccountId: {account_id}")
        
        if message_body == "hi":
            reply_text = (
                "Welcome to our Clinic Assistant! How can we help you today?\n\n"
                "1. Book Appointment\n"
                "2. Cancel Appointment\n"
                "3. Clinic Location\n\n"
                "Please reply with the number of your choice.haha"
            )
            
            r = requests.post(
                f"https://zernio.com/api/v1/inbox/conversations/{conversation_id}/messages",
                headers={
                    "Authorization": f"Bearer {ZERNIO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "accountId": account_id,
                    "message": reply_text
                }
            )
            
            print(f"Reply status: {r.status_code}, Response: {r.text}")
    
    return JSONResponse(content={"status": "processed"}, status_code=status.HTTP_200_OK)