"""MCP Server: proper FastMCP tool registration. Runs via stdio transport."""

import os
import logging
from datetime import datetime
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("parking-reservations")

# Output file path from environment (passed by client at spawn)
OUTPUT_FILE = os.getenv("MCP_OUTPUT_FILE", "confirmed_reservations.txt")


# Register tool using @mcp.tool() decorator
@mcp.tool()
def write_reservation(
    reservation_id: int,
    first_name: str,
    last_name: str,
    license_plate: str,
    start_time: str,
    end_time: str,
) -> str:
    """Write an approved parking reservation to the confirmed reservations file.

    Args:
        reservation_id: Database ID of the reservation
        first_name: Customer first name
        last_name: Customer last name
        license_plate: Vehicle license plate number
        start_time: Reservation start datetime
        end_time: Reservation end datetime

    Returns:
        Confirmation message with the written line
    """
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"{first_name} {last_name} | {license_plate} | "
            f"{start_time} - {end_time} | {approval_time}")

    with open(OUTPUT_FILE, "a") as f:
        f.write(line + "\n")

    logger.info("Written: %s", line)
    return f"Reservation #{reservation_id} written: {line}"


# Run via stdio when executed directly
if __name__ == "__main__":
    mcp.run()