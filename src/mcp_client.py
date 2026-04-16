"""MCP Client: connects to MCP server via stdio transport using SDK ClientSession."""

import os
import asyncio
import logging
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.models import Reservation
from src.config import MCP_SERVER_SCRIPT, MCP_OUTPUT_FILE, MCP_FALLBACK_ENABLED

logger = logging.getLogger(__name__)


# Async function using MCP SDK ClientSession + stdio_client
async def _call_write_reservation_async(reservation: Reservation) -> dict:
    """Connect to MCP server via stdio, call write_reservation tool."""

    server_params = StdioServerParameters(
        command="python",
        args=[MCP_SERVER_SCRIPT],
        env={**os.environ, "MCP_OUTPUT_FILE": MCP_OUTPUT_FILE},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover tools via protocol
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            logger.info("MCP tools available: %s", tool_names)

            # Call tool via MCP protocol
            result = await session.call_tool(
                "write_reservation",
                arguments={
                    "reservation_id": reservation.id,
                    "first_name": reservation.first_name,
                    "last_name": reservation.last_name,
                    "license_plate": reservation.license_plate,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                }
            )

            # Parse MCP CallToolResult
            text = result.content[0].text if result.content else "Written"
            is_error = getattr(result, "isError", False)

            if is_error:
                logger.error("MCP tool returned error: %s", text)
                return {"success": False, "message": text}

            logger.info("MCP tool success: %s", text)
            return {"success": True, "message": text}


# Sync wrapper — handles event loop for non-async callers
def call_write_reservation(reservation: Reservation) -> dict:
    try:
        return asyncio.run(_call_write_reservation_async(reservation))

    except Exception as e:
        logger.error("MCP call failed: %s", e)

        if MCP_FALLBACK_ENABLED:
            logger.warning("MCP_FALLBACK_ENABLED=true — writing locally")
            return local_fallback(reservation)
        else:
            logger.error("MCP_FALLBACK_ENABLED=false — write FAILED")
            return {
                "success": False,
                "message": f"MCP server unavailable and fallback disabled: {e}",
            }


# Fallback: direct file write (no MCP protocol)
def local_fallback(reservation: Reservation) -> dict:
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{reservation.file_line} | {approval_time}"
    with open(MCP_OUTPUT_FILE, "a") as f:
        f.write(line + "\n")
    logger.warning("Wrote locally (fallback): %s", line)
    return {"success": True, "message": "Written locally (fallback)", "line": line}