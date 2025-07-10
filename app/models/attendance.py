from pydantic import BaseModel
from typing import Literal

class AttendanceMark(BaseModel):
    user_id: str
    date: str  # Format: YYYY-MM-DD
    status: Literal["present", "absent", "late"]
