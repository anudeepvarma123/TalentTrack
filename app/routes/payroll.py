from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime
from bson import ObjectId
from app.db.mongo import db
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", summary="Generate salary (form)")
async def generate_salary(
    employee_id: str = Form(""),
    base_salary: float = Form(""),
    bonus: float = Form(""),
    deductions: float = Form(""),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can generate payroll")

    total_salary = base_salary + bonus - deductions
    payroll_data = {
        "employee_id": employee_id,
        "base_salary": base_salary,
        "bonus": bonus,
        "deductions": deductions,
        "total_salary": total_salary,
        "generated_at": datetime.utcnow()
    }

    result = await db.payrolls.insert_one(payroll_data)
    return {"message": "Payroll generated", "id": str(result.inserted_id)}

@router.get("/", summary="List all payrolls")
async def list_payrolls(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    payrolls = await db.payrolls.find().to_list(length=100)
    for p in payrolls:
        p["_id"] = str(p["_id"])
    return payrolls

@router.get("/employee/{employee_id}", summary="View payrolls for an employee")
async def employee_payrolls(employee_id: str, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "employee"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if user["role"] == "employee" and user["user_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    payrolls = await db.payrolls.find({"employee_id": employee_id}).to_list(length=100)
    for p in payrolls:
        p["_id"] = str(p["_id"])
    return payrolls
