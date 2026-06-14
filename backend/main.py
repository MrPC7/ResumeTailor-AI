import shutil
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# google.api_core emits a FutureWarning on Python 3.10 about its upcoming EOL.
# Suppress it until the venv is migrated to Python 3.11+.
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

from api.analyze_jd import router as analyze_jd_router
from api.ats import router as ats_router
from api.customize_resume import router as customize_resume_router
from api.export import router as export_router
from api.extract_resume import router as extract_resume_router
from api.parse_resume import router as parse_resume_router
from api.router import api_router
from api.upload import router as upload_router
from core.config import settings
from core.logging import setup_logging
from core.middleware import MaxBodySizeMiddleware

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()

# ---------------------------------------------------------------------------
# Rate limiter (in-memory; use Redis backend for multi-process)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=[])


# ---------------------------------------------------------------------------
# Lifespan: clean up temp uploads on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    upload_dir = Path(settings.TEMP_UPLOAD_DIR)
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
    upload_dir.mkdir(parents=True, exist_ok=True)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.MAX_REQUEST_BODY_BYTES)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(upload_router, prefix="/api")
app.include_router(parse_resume_router, prefix="/api")
app.include_router(extract_resume_router, prefix="/api")
app.include_router(analyze_jd_router, prefix="/api")
app.include_router(customize_resume_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(ats_router, prefix="/api")
