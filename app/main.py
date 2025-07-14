from fastapi import FastAPI
from app.routes import auth, employee, leave
from app.routes import payroll,attendance

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(employee.router, prefix="/employees", tags=["Employees"])
app.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"]) 
app.include_router(leave.router, prefix="/leaves", tags=["Leaves"])


# Root endpoint
@app.get("/")
def home():
    return {"message": "Welcome to TalentTrack HRM System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)