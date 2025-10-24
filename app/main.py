from fastapi import FastAPI
from app.config.database import engine, Base
from app.routes import auth_routes, resident_routes, admin_routes

# Import models to create tables
from app.models import user, slot, visitor, request

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apartment Parking System", version="1.0")

# Include routes
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(resident_routes.router, prefix="/resident", tags=["Resident"])
app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "Apartment Parking Slot Booking API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}