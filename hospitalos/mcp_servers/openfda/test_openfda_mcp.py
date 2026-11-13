"""
test_openfda_mcp.py — Manual test script for the openFDA MCP server (needs internet).

Run from the hospitalos/ folder:
  python mcp_servers/openfda/test_openfda_mcp.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "server.py"


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    print("=== Testing HospitalOS-openFDA MCP Server ===")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            for name, args in [
                ("drug_label_info", {"drug_name": "ibuprofen"}),
                ("drug_adverse_events", {"drug_name": "amoxicillin", "limit": 3}),
                ("drug_label_info", {"drug_name": "<bad input>"}),
            ]:
                result = await session.call_tool(name, args)
                print(f"\n--- {name}({args}) ---")
                print(result.content[0].text[:800])


if __name__ == "__main__":
    asyncio.run(main())
