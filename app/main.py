from fastapi import FastAPI
from app.routes import auth, employee
from app.routes import payroll

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(employee.router, prefix="/employees", tags=["Employees"])
app.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])

# Root endpoint
@app.get("/")
def home():
    return {"message": "Welcome to TalentTrack HRM System"}
