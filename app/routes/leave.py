from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime
from bson import ObjectId
from app.db.mongo import db
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", summary="Apply for leave (form)")
async def apply_leave(
    from_date: str = Form(" "),
    to_date: str = Form(" "),
    reason: str = Form(" "),
    user=Depends(get_current_user)
):
    if user["role"] not in ["employee", "hr", "admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    leave_request = {
        "user_id": user["user_id"],
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason,
        "status": "pending",
        "applied_at": datetime.utcnow()
    }

    result = await db.leaves.insert_one(leave_request)
    return {"message": "Leave applied", "id": str(result.inserted_id)}

@router.get("/", summary="View all leave requests")
async def view_all_leaves(user=Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    leaves = await db.leaves.find().to_list(length=100)
    for leave in leaves:
        leave["_id"] = str(leave["_id"])
    return leaves

@router.get("/me", summary="View my leave requests")
async def view_my_leaves(user=Depends(get_current_user)):
    leaves = await db.leaves.find({"user_id": user["user_id"]}).to_list(length=100)
    for leave in leaves:
        leave["_id"] = str(leave["_id"])
    return leaves

@router.put("/{id}/status", summary="Approve or reject leave (form)")
async def update_leave_status(
    id: str,
    status: str = Form(...),  # "approved" or "rejected"
    user=Depends(get_current_user)
):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can update leave status")

    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await db.leaves.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": status, "processed_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found")

    return {"message": f"Leave {status}"}
