from pydantic import BaseModel
from typing import Optional

class EmployeeBase(BaseModel):
    name: str
    email: str
    department: str
    role: str
    joining_date: str 
    userid:str # Format: YYYY-MM-DD

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str]
    email: Optional[str]
    department: Optional[str]
    role: Optional[str]
    joining_date: Optional[str]
    
