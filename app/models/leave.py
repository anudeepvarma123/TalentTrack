from pydantic import BaseModel
from typing import Optional, Literal

class LeaveRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str
    reason: Optional[str] = ""
    status: Optional[Literal["pending", "approved", "rejected"]] = "pending"
