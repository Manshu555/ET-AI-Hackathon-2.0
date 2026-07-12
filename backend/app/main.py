from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()

# Import all routers
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as documents_router
from app.modules.rfi.router import router as rfi_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.compliance.router import router as compliance_router
from app.modules.projects.router import router as projects_router
from app.modules.schedule.router import router as schedule_router
from app.modules.supply_chain.router import router as supply_chain_router
from app.modules.commissioning.router import router as commissioning_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Intelligence Platform for Data Centre EPC Project Delivery",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Register global exception handlers
register_exception_handlers(app)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all module routers ──────────────────────────────────
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(compliance_router, prefix=f"{settings.API_V1_STR}/compliance", tags=["compliance"])
app.include_router(schedule_router, prefix=f"{settings.API_V1_STR}/schedule", tags=["schedule"])
app.include_router(supply_chain_router, prefix=f"{settings.API_V1_STR}/shipments", tags=["supply-chain"])
app.include_router(commissioning_router, prefix=f"{settings.API_V1_STR}/commissioning", tags=["commissioning"])
app.include_router(rfi_router, prefix=f"{settings.API_V1_STR}/rfi", tags=["rfi"])
app.include_router(dashboard_router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "EPC-Intel API"}
