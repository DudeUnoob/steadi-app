from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
<<<<<<< HEAD
from app.routers import auth_router, inventory_router
from app.api.mvp.dashboard import router as dashboard_router
=======
from app.routers import auth as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.edit import router as edit_router
from app.routers.alerts import router as alerts_router
>>>>>>> 845ba7252a2313f5c73814cf017aad057bcbb0a7
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Create the FastAPI application
app = FastAPI(
    title="Steadi API",
    description="API for Steadi - AI Agent for Small Businesses",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant ID middleware
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # For multi-tenant isolation
    tenant_id = request.headers.get("X-Tenant-ID")
    # Add tenant_id to request state if needed
    # request.state.tenant_id = tenant_id
    response = await call_next(request)
    return response

# Include routers
<<<<<<< HEAD
app.include_router(auth_router)
app.include_router(inventory_router)
=======
app.include_router(auth_router.router)
>>>>>>> 845ba7252a2313f5c73814cf017aad057bcbb0a7
app.include_router(dashboard_router)
app.include_router(edit_router)
app.include_router(alerts_router)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Steadi API"}
