from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timedelta
from app.db.mongo import db
from app.auth.dependencies import get_current_user
import subprocess
from typing import Optional

router = APIRouter()
AUTHORIZED_SSID = "COMITIFS"

# 🛠 Get connected Wi-Fi SSID (Windows)
def get_connected_ssid() -> Optional[str]:
    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], shell=True)
        output = result.decode("utf-8")
        for line in output.splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":", 1)[1].strip()
    except Exception:
        return None
    return None

# 🧠 Get employee details
async def get_employee_details(user_id: str):
    return await db.employees.find_one({"user_id": {"$regex": f"^{user_id}$", "$options": "i"}})

@router.post("/", summary="Mark attendance (only on authorized Wi-Fi)")
async def mark_attendance(
    status: str = Form(..., description="present/absent/late"),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr", "employee"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # ✅ Check if connected to the allowed Wi-Fi
    ssid = get_connected_ssid()
    if ssid != AUTHORIZED_SSID:
        raise HTTPException(status_code=403, detail="You are not connected to authorized Wi-Fi")

    # 🗓 Use current UTC date
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # ✅ Prevent duplicate present for today
    if status.lower() == "present":
        existing = await db.attendance.find_one({
            "user_id": user["user_id"],
            "date": today,
            "status": "present"
        })
        if existing:
            raise HTTPException(status_code=400, detail="Already marked present for today")

    record = {
        "user_id": user["user_id"],
        "status": status,
        "date": today,
        "timestamp": datetime.utcnow()
    }

    await db.attendance.insert_one(record)
    return {"message": "Attendance marked successfully"}

    # ❌ Prevent duplicate marking for the same date
    check = await db.attendance.find_one({
        "user_id": user["user_id"],
        "date": today
    })
    if check:
        raise HTTPException(status_code=400, detail="Attendance already marked for today")

    record = {
        "user_id": user["user_id"],
        "status": status,
        "date": today,
        "timestamp": datetime.utcnow()
    }

    await db.attendance.insert_one(record)
    return {"message": "Attendance marked successfully"}

# 📜 Employee: view my attendance history
@router.get("/me", summary="View my attendance history")
async def view_my_attendance(user=Depends(get_current_user)):
    records = await db.attendance.find({"user_id": user["user_id"]}).sort("date", -1).to_list(length=200)
    for r in records:
        r["_id"] = str(r["_id"])
    return {"user_id": user["user_id"], "attendance": records}

# 🧑‍💼 Admin: view all records with employee info
@router.get("/", summary="Admin/HR: View all attendance records")
async def view_all_attendance(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    records = await db.attendance.find().sort("date", -1).to_list(length=300)
    enriched = []
    for r in records:
        emp = await get_employee_details(r["user_id"])
        r["_id"] = str(r["_id"])
        if emp:
            r["employee"] = {
                "name": emp["name"],
                "department": emp["department"],
                "role": emp["role"]
            }
        enriched.append(r)
    return enriched

# 📅 Admin: view all employees present today
@router.get("/present-today", summary="Admin: View today's present employees")
async def view_present_today(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    records = await db.attendance.find({"date": today, "status": "present"}).to_list(length=100)
    enriched = []
    for r in records:
        emp = await get_employee_details(r["user_id"])
        r["_id"] = str(r["_id"])
        if emp:
            r["employee"] = {
                "name": emp["name"],
                "department": emp["department"],
                "role": emp["role"]
            }
        enriched.append(r)
    return enriched

# 👤 Admin: view attendance of a specific employee
@router.get("/{user_id}", summary="Admin: View attendance by employee user_id")
async def view_employee_attendance(user_id: str, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    records = await db.attendance.find({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    }).sort("date", -1).to_list(length=100)

    emp = await get_employee_details(user_id)
    enriched = []
    for r in records:
        r["_id"] = str(r["_id"])
        if emp:
            r["employee"] = {
                "name": emp["name"],
                "department": emp["department"],
                "role": emp["role"]
            }
        enriched.append(r)

    return enriched
