import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# google.api_core emits a FutureWarning on Python 3.10 about its upcoming EOL.
# Suppress it until the venv is migrated to Python 3.11+.
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

from api.analyze_jd import router as analyze_jd_router
from api.extract_resume import router as extract_resume_router
from api.match_score import router as match_score_router
from api.parse_resume import router as parse_resume_router
from api.router import api_router
from api.upload import router as upload_router
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(upload_router, prefix="/api")
app.include_router(parse_resume_router, prefix="/api")
app.include_router(extract_resume_router, prefix="/api")
app.include_router(analyze_jd_router, prefix="/api")
app.include_router(match_score_router, prefix="/api")
