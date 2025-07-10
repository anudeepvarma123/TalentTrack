# app/models/payroll.py

from pydantic import BaseModel

class Payroll(BaseModel):
    employee_id: str
    base_salary: float
    bonus: float = 0.0
    deductions: float = 0.0
