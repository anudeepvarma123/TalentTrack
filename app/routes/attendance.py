from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime
from app.db.mongo import db
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", summary="Mark attendance (form)")
async def mark_attendance(
    status: str = Form(" "),  # e.g., "present", "absent", "late"
    date: str = Form(None),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr", "employee"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    attendance_date = date or datetime.utcnow().strftime('%Y-%m-%d')

    existing = await db.attendance.find_one({
        "user_id": user["user_id"],
        "date": attendance_date
    })

    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")

    record = {
        "user_id": user["user_id"],
        "status": status,
        "date": attendance_date,
        "timestamp": datetime.utcnow()
    }

    await db.attendance.insert_one(record)
    return {"message": "Attendance marked"}

@router.get("/", summary="View all attendance")
async def view_all_attendance(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    records = await db.attendance.find().to_list(length=100)
    for r in records:
        r["_id"] = str(r["_id"])
    return records

@router.get("/me", summary="View my attendance")
async def view_my_attendance(user=Depends(get_current_user)):
    records = await db.attendance.find({"user_id": user["user_id"]}).to_list(length=100)
    for r in records:
        r["_id"] = str(r["_id"])
    return records
