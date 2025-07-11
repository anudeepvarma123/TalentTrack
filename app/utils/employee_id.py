from app.db.mongo import db  # use the shared Motor client from your database config

async def get_next_employee_id():
    result = await db.counters.find_one_and_update(
        {"_id": "employeeId"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return f"EMP{result['seq']:03d}"  # EMP001, EMP002, etc.
