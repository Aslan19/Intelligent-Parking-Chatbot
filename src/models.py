"""✅ CHANGE #6: Pydantic Reservation model replaces plain dicts."""

from typing import Optional
from pydantic import BaseModel, Field


class Reservation(BaseModel):
    """Validated reservation model used across all modules."""
    id: Optional[int] = None
    first_name: str
    last_name: str
    license_plate: str
    start_time: str
    end_time: str
    status: str = "pending_approval"
    admin_comment: str = ""
    created_at: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def file_line(self) -> str:
        return (f"{self.full_name} | {self.license_plate} | "
                f"{self.start_time} - {self.end_time}")


class ReservationCreate(BaseModel):
    """Fields required to create a reservation."""
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    license_plate: str = Field(..., min_length=1)
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)


class ReservationRecord(BaseModel):
    """MCP server inbound payload."""
    reservation_id: int
    first_name: str
    last_name: str
    license_plate: str
    start_time: str
    end_time: str