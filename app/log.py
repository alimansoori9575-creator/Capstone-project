import os
import json
import time
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "requests.jsonl")

def log_request(endpoint: str, payload: dict, response: dict, execution_time_ms: float):
    # generate a unique trace id for this specific request
    trace_id = str(uuid.uuid4())
    
    log_entry = {
        "trace_id": trace_id,
        "timestamp": time.time(),
        "endpoint": endpoint,
        "execution_time_ms": round(execution_time_ms, 2),
        "request_payload": payload,
        "response_payload": response
    }
    
    # append to json-lines file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return trace_id