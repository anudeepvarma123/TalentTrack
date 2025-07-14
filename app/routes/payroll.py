from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime
from app.db.mongo import db
from app.auth.dependencies import get_current_user

router = APIRouter()

def serialize_document(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.post("/", summary="Generate payroll (form)")
async def generate_salary(
    user_id: str = Form(""),
    base_salary: float = Form(""),
    bonus: float = Form(0.0),
    deductions: float = Form(""),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can generate payroll")

    # 🔍 Check if employee exists
    employee = await db.employees.find_one({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee with given user_id not found")

    # ❌ Prevent duplicate payroll entry
    existing = await db.payrolls.find_one({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Payroll already exists for this employee. Use update.")

    total_salary = base_salary + bonus - deductions

    payroll_data = {
        "user_id": employee["user_id"],
        "employee_name": employee["name"],
        "base_salary": base_salary,
        "bonus": bonus,
        "deductions": deductions,
        "total_salary": total_salary,
        "generated_at": datetime.utcnow()
    }

    result = await db.payrolls.insert_one(payroll_data)
    return {
        "message": "Payroll generated successfully",
        "employee": {
            "user_id": employee["user_id"],
            "name": employee["name"],
            "department": employee["department"],
            "total_salary": total_salary
        }
    }

@router.put("/{user_id}", summary="Update payroll details")
async def update_payroll(
    user_id: str,
    base_salary: float = Form(...),
    bonus: float = Form(0.0),
    deductions: float = Form(...),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can update payroll")

    # 🔍 Validate payroll exists
    existing = await db.payrolls.find_one({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Payroll not found for this employee")

    total_salary = base_salary + bonus - deductions

    update_result = await db.payrolls.update_one(
        {"user_id": {"$regex": f"^{user_id}$", "$options": "i"}},
        {
            "$set": {
                "base_salary": base_salary,
                "bonus": bonus,
                "deductions": deductions,
                "total_salary": total_salary,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Payroll updated successfully", "total_salary": total_salary}

@router.get("/", summary="List all payrolls")
async def list_payrolls(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    payrolls = await db.payrolls.find().to_list(length=100)
    return [serialize_document(p) for p in payrolls]

@router.get("/employee/{user_id}", summary="View payrolls for an employee")
async def employee_payrolls(user_id: str, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "employee"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if user["role"] == "employee" and user["user_id"].lower() != user_id.lower():
        raise HTTPException(status_code=403, detail="Access denied")

    payrolls = await db.payrolls.find({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    }).to_list(length=100)

    return [serialize_document(p) for p in payrolls]
