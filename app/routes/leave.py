from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, date
from bson import ObjectId
from app.db.mongo import db
from app.auth.dependencies import get_current_user
from enum import Enum
from collections import defaultdict

router = APIRouter()

MAX_ANNUAL_LEAVES = 20

class LeaveType(str, Enum):
    leave = "leave"
    wfh = "work from home"
    floater = "floater leave"

def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def serialize_leave(leave, employee=None):
    leave["_id"] = str(leave["_id"])
    if employee:
        leave["employee"] = {
            "user_id": employee.get("user_id"),
            "name": employee.get("name"),
            "email": employee.get("email"),
            "department": employee.get("department"),
            "role": employee.get("role"),
            "joining_date": employee.get("joining_date"),
        }
    return leave

# 🚀 Apply for leave
@router.post("/", summary="Apply for leave (form)")
async def apply_leave(
    leave_type: LeaveType = Form(...),
    from_date: str = Form(...),
    to_date: str = Form(...),
    reason: str = Form(...),
    user=Depends(get_current_user)
):
    user_id = user["user_id"]

    employee = await db.employees.find_one({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    from_dt = parse_date(from_date)
    to_dt = parse_date(to_date)

    if to_dt < from_dt:
        raise HTTPException(status_code=400, detail="To date must be after or equal to from date")

    days_requested = (to_dt - from_dt).days + 1

    # Approved leaves so far this year
    current_year = datetime.utcnow().year
    start_of_year = datetime(current_year, 1, 1)

    leave_stats = await db.leaves.aggregate([
        {
            "$match": {
                "user_id": {"$regex": f"^{user_id}$", "$options": "i"},
                "status": "approved",
                "applied_at": {"$gte": start_of_year}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_days": {"$sum": "$days_requested"}
            }
        }
    ]).to_list(1)

    taken_days = leave_stats[0]["total_days"] if leave_stats else 0
    if taken_days + days_requested > MAX_ANNUAL_LEAVES:
        remaining = MAX_ANNUAL_LEAVES - taken_days
        raise HTTPException(status_code=400, detail=f"Leave quota exceeded. You have {remaining} days left.")

    leave_data = {
        "user_id": employee["user_id"],
        "type": leave_type.value,
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason,
        "status": "pending",
        "days_requested": days_requested,
        "applied_at": datetime.utcnow()
    }

    result = await db.leaves.insert_one(leave_data)
    return {
        "message": "Leave applied successfully",
        "available_leaves": MAX_ANNUAL_LEAVES - taken_days - days_requested,
        "requested_days": days_requested,
        "id": str(result.inserted_id)
    }

# 🧾 All leaves with employee details
@router.get("/", summary="View all leave requests")
async def view_all_leaves(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    leaves = await db.leaves.find().to_list(200)
    results = []
    for leave in leaves:
        emp = await db.employees.find_one({
            "user_id": {"$regex": f"^{leave['user_id']}$", "$options": "i"}
        })
        results.append(serialize_leave(leave, emp))
    return results

# 👤 My leaves
@router.get("/me", summary="View my leaves and available quota")
async def view_my_leaves(user=Depends(get_current_user)):
    user_id = user["user_id"]

    leaves = await db.leaves.find({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    }).to_list(100)

    current_year = datetime.utcnow().year
    start_of_year = datetime(current_year, 1, 1)

    taken = await db.leaves.aggregate([
        {
            "$match": {
                "user_id": {"$regex": f"^{user_id}$", "$options": "i"},
                "status": "approved",
                "applied_at": {"$gte": start_of_year}
            }
        },
        {
            "$group": {"_id": None, "total": {"$sum": "$days_requested"}}
        }
    ]).to_list(1)

    used = taken[0]["total"] if taken else 0
    emp = await db.employees.find_one({
        "user_id": {"$regex": f"^{user_id}$", "$options": "i"}
    })

    return {
        "available_leaves": MAX_ANNUAL_LEAVES - used,
        "used_leaves": used,
        "history": [serialize_leave(l, emp) for l in leaves]
    }

# ✅ Update leave status (approve/reject)
@router.put("/{user_id}/status", summary="Update latest pending leave status for user_id")
async def update_leave_status_by_user_id(
    user_id: str,
    status: str = Form(...),
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can update leave status")

    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Find the latest pending leave for the given user_id
    leave = await db.leaves.find_one(
        {
            "user_id": {"$regex": f"^{user_id}$", "$options": "i"},
            "status": "pending"
        },
        sort=[("applied_at", -1)]
    )

    if not leave:
        raise HTTPException(status_code=404, detail="No pending leave found for this user_id")

    await db.leaves.update_one(
        {"_id": leave["_id"]},
        {"$set": {"status": status, "processed_at": datetime.utcnow()}}
    )

    return {
        "message": f"Leave {status}",
        "user_id": user_id,
        "leave_id": str(leave["_id"])
    }
# 🗓 Calendar grouped by month
@router.get("/calendar", summary="Leave calendar grouped by month")
async def leave_calendar(user=Depends(get_current_user)):
    query = {"status": "approved"}
    if user["role"] == "employee":
        query["user_id"] = {"$regex": f"^{user['user_id']}$", "$options": "i"}

    leaves = await db.leaves.find(query).to_list(200)
    calendar = defaultdict(list)

    for leave in leaves:
        from_dt = parse_date(leave["from_date"])
        month = from_dt.strftime("%B %Y")
        emp = await db.employees.find_one({
            "user_id": {"$regex": f"^{leave['user_id']}$", "$options": "i"}
        })
        calendar[month].append(serialize_leave(leave, emp))

    return dict(calendar)

# 📊 View by status (approved / pending / rejected)
@router.get("/status/{status}", summary="Get leaves filtered by status")
async def leaves_by_status(status: str, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    leaves = await db.leaves.find({"status": status}).to_list(100)
    result = []
    for leave in leaves:
        emp = await db.employees.find_one({
            "user_id": {"$regex": f"^{leave['user_id']}$", "$options": "i"}
        })
        result.append(serialize_leave(leave, emp))

    return result
