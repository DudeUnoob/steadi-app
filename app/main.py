from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.routers import auth_router, inventory_router
from app.routers import auth as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.edit import router as edit_router
from app.routers.alerts import router as alerts_router
from app.routers.cron import router as cron_router
from app.routers.supabase_auth import router as supabase_auth_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Steadi API",
    description="API for Steadi - AI Agent for Small Businesses",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID")
    response = await call_next(request)
    return response

app.include_router(auth_router.router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(edit_router)
app.include_router(alerts_router)
app.include_router(cron_router)
app.include_router(supabase_auth_router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to the Steadi API"}
