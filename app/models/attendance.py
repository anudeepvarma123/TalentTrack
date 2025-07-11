from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class AttendanceEntry(BaseModel):
    employee_id: str = Field(..., example="")
    status: str = Field(..., example="")  # e.g., Present, Absent, Leave
    date: Optional[date] = Field(default_factory=date.today, example="") 