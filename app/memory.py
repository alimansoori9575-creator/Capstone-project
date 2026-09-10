import os
import json
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Set up our data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "checkpoints.sqlite")
HISTORY_FILE = os.path.join(DATA_DIR, "conversation_history.json")

os.makedirs(DATA_DIR, exist_ok=True)

async def get_async_checkpointer() -> AsyncSqliteSaver:
    # Create an async connection to our sqlite database
    conn = await aiosqlite.connect(DB_FILE)
    return AsyncSqliteSaver(conn)

def save_conversation_history(history: list):
    # dump the chat array to json so we can grade it later
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def load_conversation_history() -> list:
    # load it back if it exists
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []