from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import time
import logging
import asyncio
from app.db.database import init_db, engine
from app.routers import auth as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.edit import router as edit_router
from app.routers.alerts import router as alerts_router
from app.routers.cron import router as cron_router
from app.routers.supabase_auth import router as supabase_auth_router
from app.routers.rules import router as rules_router
from app.routers.inventory import router as inventory_router
from app.routers.connectors import router as connectors_router
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Background tasks for cleanup and optimization
background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    
    # Start background optimization tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    background_tasks.add(cleanup_task)
    cleanup_task.add_done_callback(background_tasks.discard)
    
    yield
    
    # Shutdown
    logger.info("Shutting down background tasks...")
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    
    # Close database connections
    engine.dispose()
    logger.info("Application shutdown complete")

async def periodic_cleanup():
    """Background task for periodic cleanup and optimization"""
    while True:
        try:
            # Wait 30 minutes between cleanup cycles
            await asyncio.sleep(1800)
            
            # Perform database connection pool cleanup
            logger.info("Performing periodic cleanup...")
            
            # You can add more cleanup tasks here
            # - Clear expired cache entries
            # - Database maintenance
            # - Log rotation
            
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

app = FastAPI(
    title="Steadi API",
    description="API for Steadi - AI Agent for Small Businesses",
    version="0.1.0",
    lifespan=lifespan
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    # Skip logging for health checks
    if path != "/health":
        logger.info(f"Request: {method} {path}")
    
    # Get tenant ID if present
    tenant_id = request.headers.get("X-Tenant-ID")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # Log if request takes more than 1 second
        logger.warning(f"Slow request: {method} {path} - {process_time:.2f}s")
    elif path != "/health":
        logger.info(f"Response: {method} {path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
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
app.include_router(connectors_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Steadi API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": time.time()}
