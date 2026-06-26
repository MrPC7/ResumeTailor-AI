import shutil
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

# google.api_core emits a FutureWarning on Python 3.10 about its upcoming EOL.
# Suppress it until the venv is migrated to Python 3.11+.
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

from api.analyze_jd import router as analyze_jd_router
from api.cover_letter import router as cover_letter_router
from api.customize_resume import router as customize_resume_router
from api.evaluate import router as evaluate_router
from api.export import router as export_router
from api.extract_resume import router as extract_resume_router
from api.parse_resume import router as parse_resume_router
from api.router import api_router
from core.config import limiter, settings
from core.errors import (
    AppError,
    error_response,
    handle_app_error,
    handle_http_exception,
    handle_unexpected_exception,
    handle_validation_exception,
)
from core.logging import setup_logging
from core.middleware import MaxBodySizeMiddleware

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()


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
app.add_exception_handler(AppError, handle_app_error)
app.add_exception_handler(StarletteHTTPException, handle_http_exception)
app.add_exception_handler(RequestValidationError, handle_validation_exception)
app.add_exception_handler(Exception, handle_unexpected_exception)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(
    _request: Request,
    _exc: RateLimitExceeded,
):
    return error_response(
        429,
        "RATE_LIMITED",
        "Too many requests. Please wait and try again.",
    )

app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.MAX_REQUEST_BODY_BYTES)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(parse_resume_router, prefix="/api")
app.include_router(extract_resume_router, prefix="/api")
app.include_router(analyze_jd_router, prefix="/api")
app.include_router(customize_resume_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(evaluate_router, prefix="/api")
app.include_router(cover_letter_router, prefix="/api")
