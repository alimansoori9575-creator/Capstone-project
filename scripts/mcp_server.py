import os
import sys

# Add the parent directory to Python's path so it can find the 'app' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from app.tools import check_support_ticket_status

# Initialize the MCP Server
mcp = FastMCP("Ola Support MCP Server")

@mcp.tool()
def get_ticket_status(ticket_id: str) -> str:
    """
    Look up an Ola support ticket by its ID to get status and escalation details.
    """
    result = check_support_ticket_status(ticket_id)
    
    if "error" in result:
        return f"Error: {result['error']}"
        
    return (
        f"Ticket {result['record_id']} is currently {result['status']}. "
        f"Resolution time: {result['resolution_time_hours']} hours. "
        f"Escalation Score: {result['escalation_score']} -> Action: {result['recommended_action']}."
    )
if __name__ == "__main__":
    mcp.run()