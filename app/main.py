from fastapi import FastAPI
from app.routes import auth, employee, leave
from app.routes import payroll,attendance
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Specific origin for Angular dev server
    allow_credentials=True,
    allow_methods=["*"],                      # Allow all HTTP methods
    allow_headers=["*"],                      # Allow all headers
)


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(employee.router, prefix="/employees", tags=["Employees"])
app.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"]) 
app.include_router(leave.router, prefix="/leaves", tags=["Leaves"])


# Root endpoint
@app.get("/")
def home():
    return {"message": "Welcome to TalentTrack HRM"}

import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
