import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from eth_account.messages import encode_defunct
from eth_account import Account
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

WALLETS_FILE ="wallets.json"

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html manually at root
@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

def load_wallets():
    if not os.path.exists(WALLETS_FILE):
        return {}
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(data):
    with open(WALLETS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# In-memory "DB" for testing
tag_to_wallet = load_wallets()

# Data model for tag registration
class TagRegistration(BaseModel):
    tag: str
    wallet: str
    signature: str

@app.post("/register")
def register(data: TagRegistration):
    message_text = f"Registering tag {data.tag} for Project Flippi"
    message = encode_defunct(text=message_text)

    try:
        recovered_wallet = Account.recover_message(message, signature=data.signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")

    if recovered_wallet.lower() != data.wallet.lower():
        raise HTTPException(status_code=400, detail="Signature does not match wallet.")

    tag_to_wallet[data.tag.lower()] = data.wallet.lower()
    save_wallets(tag_to_wallet)
    
    return {"status": "success", "wallet": data.wallet, "tag": data.tag}

@app.get("/wallets/{tag}")
def get_wallet(tag: str):
    wallet = tag_to_wallet.get(tag.lower())
    if wallet:
        return {"wallet": wallet}
    raise HTTPException(status_code=404, detail="Tag not found")