from fastapi import FastAPI
import uvicorn
from app.routes import auth, employee
from app.routes import payroll,attendance

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(employee.router, prefix="/employees", tags=["Employees"])
app.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"]) 


# Root endpoint
@app.get("/")
def home():
    return {"message": "Welcome to TalentTrack HRM System"}

# ✅ Add this to run directly using `python main.py`
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)