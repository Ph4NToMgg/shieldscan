from contextlib import asynccontextmanager
import logging
import traceback

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from slowapi import _rate_limit_exceeded_handler
# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import init_db
from app.limiter import limiter
from app.routers import scan
from app.models.user_credits import UserCredits  # noqa: F401 — register model with Base

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory log buffer for remote debugging
debug_logs = []

class InMemoryHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            debug_logs.append(log_entry)
            if len(debug_logs) > 200:
                debug_logs.pop(0)
        except Exception:
            pass

# Configure root logger to output to our buffer
handler = InMemoryHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and run schema migrations on startup."""
    await init_db()
    
    # Run migrations: add user_id column and index to scan_results if they don't exist
    from app.database import engine
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_scan_results_user_id ON scan_results (user_id)"))
            logger.info("Database migrations (scan_results.user_id) completed successfully.")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}", exc_info=True)
        
    yield


app = FastAPI(
    title="ShieldScan",
    description="Website Security Analyzer API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/scan", tags=["scan"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return JSON so CORS headers are applied."""
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}",
            "error": str(exc),
            "traceback": tb,
        },
    )


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ShieldScan API"}


@app.get("/debug-logs", tags=["system"])
async def get_debug_logs():
    """Return the last 200 log messages from the backend."""
    return {"logs": debug_logs}

