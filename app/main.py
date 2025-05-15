from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.routers import auth as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.edit import router as edit_router
from app.routers.alerts import router as alerts_router
from app.routers.cron import router as cron_router
from app.routers.supabase_auth import router as supabase_auth_router
from app.routers.rules import router as rules_router
from app.routers.inventory import router as inventory_router
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Steadi API",
    description="API for Steadi - AI Agent for Small Businesses",
    version="0.1.0"
)

# Add CORS middleware with more permissive settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "*"  # Allow all origins in development - REMOVE IN PRODUCTION
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Log requests for debugging
    path = request.url.path
    method = request.method
    logger.info(f"Request: {method} {path}")
    
    # Get tenant ID if present
    tenant_id = request.headers.get("X-Tenant-ID")
    
    # Process the request
    response = await call_next(request)
    
    # Log response status
    logger.info(f"Response: {method} {path} - Status: {response.status_code}")
    
    return response

# Include all routers
app.include_router(auth_router.router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(edit_router)
app.include_router(alerts_router)
app.include_router(cron_router)
app.include_router(supabase_auth_router)
app.include_router(rules_router)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

@app.get("/")
async def root():
    return {"message": "Welcome to the Steadi API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}
