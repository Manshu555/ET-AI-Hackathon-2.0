from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as documents_router
from app.modules.rfi.router import router as rfi_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.modules.dashboard.router import router as dashboard_router
from app.modules.compliance.router import router as compliance_router

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(rfi_router, prefix=f"{settings.API_V1_STR}/rfi", tags=["rfi"])
app.include_router(dashboard_router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(compliance_router, prefix=f"{settings.API_V1_STR}/compliance", tags=["compliance"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

