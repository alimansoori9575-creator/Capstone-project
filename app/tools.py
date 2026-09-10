import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKETS_FILE = os.path.join(BASE_DIR, "data", "tickets.json")

def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        raise FileNotFoundError(f"Tickets dataset not found at {TICKETS_FILE}. Run data/dataset.py first.")
    with open(TICKETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def check_support_ticket_status(record_id: str) -> dict:
    """
    Looks up a support ticket by record_id and calculates a designed escalation score.
    
    Escalation Score Formula:
        escalation_score = (0.6 * is_escalated) + (0.4 * (days_since_created / 30.0))
        
    - is_escalated: 1.0 if ticket is escalated, else 0.0 (Base weight: 60%)
    - recency_signal: days_since_created normalized to [0, 1] using max span of 30 days (Base weight: 40%)
    
    Escalation Threshold Recommendation:
        Threshold = 0.60
        - Any actively escalated ticket immediately starts at 0.60, triggering priority review.
        - An unescalated ticket created 25+ days ago reaches >= 0.33, signaling age but not emergency.
    """
    tickets = load_tickets()
    ticket = next((t for t in tickets if t["record_id"].strip().upper() == record_id.strip().upper()), None)
    
    if not ticket:
        return {
            "error": f"Ticket with ID '{record_id}' not found."
        }
        
    is_escalated = 1.0 if ticket.get("escalated", False) else 0.0
    recency_signal = min(ticket.get("days_since_created", 0) / 30.0, 1.0)
    
    escalation_score = round((0.6 * is_escalated) + (0.4 * recency_signal), 3)
    
    return {
        "record_id": ticket["record_id"],
        "status": ticket["status"],
        "resolution_time_hours": ticket["resolution_time_hours"],
        "days_since_created": ticket["days_since_created"],
        "escalated": ticket["escalated"],
        "escalation_score": escalation_score,
        "recommended_action": "Priority Management Escalation" if escalation_score >= 0.60 else "Standard Queue"
    }

if __name__ == "__main__":
    # Test on a known record
    print("Testing tools.py:")
    test_result = check_support_ticket_status("TICK-1001")
    print(json.dumps(test_result, indent=2))