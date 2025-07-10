from fastapi import APIRouter, HTTPException, Depends, Form
from bson import ObjectId
from app.db.mongo import db
from app.auth.dependencies import get_current_user

router = APIRouter()

def serialize_employee(emp):
    emp["_id"] = str(emp["_id"])
    return emp

@router.post("/", summary="Create employee (form)")
async def create_employee(
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    role: str = Form(...),
    joining_date: str = Form(...),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    employee_data = {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
        "joining_date": joining_date
    }

    result = await db.employees.insert_one(employee_data)
    return {"message": "Employee created", "id": str(result.inserted_id)}

@router.get("/", summary="List all employees")
async def list_employees(user=Depends(get_current_user)):
    employees = await db.employees.find().to_list(length=100)
    return [serialize_employee(e) for e in employees]

@router.get("/{id}", summary="Get single employee")
async def get_employee(id: str, user=Depends(get_current_user)):
    employee = await db.employees.find_one({"_id": ObjectId(id)})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return serialize_employee(employee)

@router.put("/{id}", summary="Update employee (form)")
async def update_employee(
    id: str,
    name: str = Form(None),
    email: str = Form(None),
    department: str = Form(None),
    role: str = Form(None),
    joining_date: str = Form(None),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    update_data = {k: v for k, v in {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
        "joining_date": joining_date
    }.items() if v is not None}

    result = await db.employees.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated"}

@router.delete("/{id}", summary="Delete employee")
async def delete_employee(id: str, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete employees")
    result = await db.employees.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted"}
