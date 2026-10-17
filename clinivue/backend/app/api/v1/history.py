import os
import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
HISTORY_FILE = Path(__file__).resolve().parents[3] / "data" / "history.json"

class HistoryEntry(BaseModel):
    user_uid: str
    encrypted_data: str

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_history(data):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f)

@router.get("/{user_uid}")
def get_history(user_uid: str):
    data = load_history()
    return {"encryptedData": data.get(user_uid, "")}

@router.post("/")
def update_history(entry: HistoryEntry):
    data = load_history()
    data[entry.user_uid] = entry.encrypted_data
    save_history(data)
    return {"status": "success"}

@router.delete("/{user_uid}")
def clear_history(user_uid: str):
    data = load_history()
    if user_uid in data:
        del data[user_uid]
        save_history(data)
    return {"status": "success"}
