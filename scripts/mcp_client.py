import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    server_params = StdioServerParameters(
        command="python",
        args=["scripts/mcp_server.py"]
    )

    print("Initializing MCP Client and connecting to server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected successfully!\n")
            
            for ticket_id in ["TICK-1001", "TICK-1002"]:
                print(f"Executing tool 'get_ticket_status' for {ticket_id}...")
                result = await session.call_tool(
                    "get_ticket_status", 
                    arguments={"ticket_id": ticket_id}
                )
                print(f"--- Response ---\n{result.content[0].text}\n")

if __name__ == "__main__":
    asyncio.run(run_client())