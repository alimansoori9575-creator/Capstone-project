import asyncio
import sys
import os

# Add the parent directory to Python's path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    # The client launches the server as a background process
    server_params = StdioServerParameters(
        command="python",
        args=["scripts/mcp_server.py"]
    )

    print("Initializing MCP Client and connecting to server...")
    
    # Connect via stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected successfully!")
            
            # Request our tool
            ticket_id = "TICK-1002"
            print(f"\nExecuting tool 'get_ticket_status' for {ticket_id}...")
            
            result = await session.call_tool(
                "get_ticket_status", 
                arguments={"ticket_id": ticket_id}
            )
            
            print("\n--- MCP Server Response ---")
            print(result.content[0].text)
            print("---------------------------")

if __name__ == "__main__":
    asyncio.run(run_client())