from fastapi import FastAPI
from app.config.database import engine, Base
from app.routes import auth_routes, resident_routes, admin_routes
from app.models import user, slot, visitor, request, notification

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apartment Parking System", version="1.0")

# Include routes
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(resident_routes.router, prefix="/resident", tags=["Resident"])
app.include_router(resident_routes.router1, prefix="/resident/slot", tags=["Resident Slot"])
app.include_router(resident_routes.router2, prefix="/resident/visitors", tags=["Resident Visitors"])
app.include_router(resident_routes.router3, prefix="/resident/request", tags=["Resident Request"])
app.include_router(resident_routes.router4, prefix="/resident/notification", tags=["Resident Notification"])
# app.include_router(resident_routes.router5, prefix="/resident/dashboard", tags=["Resident Dashboard"])
app.include_router(resident_routes.router6, prefix="/resident/unplanned", tags=["Resident Unplanned Visitors"])

app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])
app.include_router(admin_routes.router1, prefix="/admin/slot", tags=["Admin Slot"])
app.include_router(admin_routes.router2, prefix="/admin/visitor", tags=["Admin Visitor"])
app.include_router(admin_routes.router3, prefix="/admin/notification", tags=["Admin Notification"])
# app.include_router(admin_routes.router4, prefix="/admin/dashboard", tags=["Admin Dashboard"])
