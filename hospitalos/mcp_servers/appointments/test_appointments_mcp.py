"""
test_appointments_mcp.py — Automated Test Script for the Appointments MCP Server.

Calls each tool once via the official MCP stdio client and prints the result:
  1. list_doctor_availability(doctor_id=1, date="2026-11-10")           [READ]
  2. list_appointments(patient_id=1)                                    [READ]
  3. book_appointment(patient_id=3, doctor_id=2, datetime="2026-11-12T10:00") [WRITE]
  4. cancel_appointment(appointment_id=7)                               [WRITE]

Run from the `hospitalos/` directory:
  python mcp_servers/appointments/test_appointments_mcp.py
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HOSPITALOS_ROOT = Path(__file__).resolve().parents[2]


async def main():
    server_script = str(HOSPITALOS_ROOT / "mcp_servers" / "appointments" / "server.py")
    server_params = StdioServerParameters(command=sys.executable, args=[server_script])

    print("=== Testing HospitalOS-Appointments MCP Server ===")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"Discovered {len(tools.tools)} tools:")
            for t in tools.tools:
                first_line = (t.description or "").strip().splitlines()[0]
                print(f"  - {t.name}: {first_line}")

            print("\n1. Calling list_doctor_availability(doctor_id=1, date='2026-11-10')...")
            r1 = await session.call_tool(
                "list_doctor_availability",
                arguments={"doctor_id": 1, "date": "2026-11-10"},
            )
            print(r1.content[0].text)

            print("\n2. Calling list_appointments(patient_id=1)...")
            r2 = await session.call_tool("list_appointments", arguments={"patient_id": 1})
            print(r2.content[0].text)

            # Always book in the future (a week from now, 11:00) so the test never goes stale
            when = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT11:00")
            print(f"\n3. Calling book_appointment(patient_id=3, doctor_id=2, datetime='{when}')...")
            r3 = await session.call_tool(
                "book_appointment",
                arguments={"patient_id": 3, "doctor_id": 2, "datetime": when},
            )
            text3 = r3.content[0].text
            print(text3)

            # Cancel ONLY the appointment we just created (never a real one)
            try:
                booked_id = json.loads(text3)["appointment"]["id"]
            except (ValueError, KeyError):
                print("\n4. Booking did not succeed, so there is nothing to cancel.")
                return

            print(f"\n4. Calling cancel_appointment(appointment_id={booked_id})...")
            r4 = await session.call_tool(
                "cancel_appointment", arguments={"appointment_id": booked_id}
            )
            print(r4.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
