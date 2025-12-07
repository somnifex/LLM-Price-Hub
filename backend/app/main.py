from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import prices, models, config, admin, auth, user_keys, settings

app = FastAPI(title="LLM Price Hub", version="0.0.1")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (for uploads)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(prices.router)
app.include_router(models.router)
app.include_router(config.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(user_keys.router)
app.include_router(settings.router)


@app.on_event("startup")
def on_startup():
    init_db()
    from app.services.scheduler import scheduler, update_exchange_rates

    # Kick off an immediate currency sync so rates are available right after boot
    try:
        update_exchange_rates()
    except Exception:
        pass

    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    from app.services.scheduler import scheduler

    scheduler.shutdown()


@app.get("/")
def read_root():
    return {"message": "LLM Price Hub API is running"}
