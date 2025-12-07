from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import prices, models, config, admin, auth, user_keys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("ENV") == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Price Hub", version="0.0.1")

# CORS - restrict in production
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if not allowed_origins_str:
    # Default to localhost for development
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
else:
    allowed_origins = allowed_origins_str.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (for uploads)
static_dir = os.getenv("STATIC_DIR", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    logger.info(f"Created static directory: {static_dir}")

try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.warning(f"Could not mount static directory: {e}")

# Routers
app.include_router(prices.router)
app.include_router(models.router)
app.include_router(config.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(user_keys.router)

@app.on_event("startup")
def on_startup():
    logger.info("Starting LLM Price Hub API...")
    init_db()
    logger.info("Database initialized")
    from app.services.scheduler import scheduler
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down LLM Price Hub API...")
    from app.services.scheduler import scheduler
    scheduler.shutdown()
    logger.info("Scheduler stopped")

@app.get("/")
def read_root():
    return {"message": "LLM Price Hub API is running"}
