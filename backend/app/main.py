from fastapi import FastAPI
from sqlalchemy import inspect, text, select
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:5000", "http://127.0.0.1:5000"],
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

@app.on_event("startup")
async def startup():
    """Auto-create all database tables on startup."""
    from app.db.base import engine, Base
    # Import all models so Base.metadata knows about them
    from app.modules.auth import models as auth_models  # noqa
    from app.modules.projects import models as project_models  # noqa
    from app.modules.documents import models as doc_models  # noqa
    from app.modules.compliance import models as comp_models  # noqa
    from app.modules.schedule import models as sched_models  # noqa
    from app.modules.supply_chain import models as sc_models  # noqa
    from app.modules.commissioning import models as comm_models  # noqa
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # `create_all` only creates missing tables; it does not add columns to
        # an existing SQLite database. Keep local/demo databases created by an
        # older version compatible with the current Document model.
        if conn.dialect.name == "sqlite":
            document_columns = await conn.run_sync(
                lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("documents")}
            )
            if "page_count" not in document_columns:
                await conn.execute(text("ALTER TABLE documents ADD COLUMN page_count INTEGER"))

    # One-time compatibility bootstrap for the original single-project demo
    # database. New projects receive membership at creation time.
    from app.db.base import async_session_maker
    from app.modules.auth.models import User
    from app.modules.projects.models import Project, ProjectMember
    async with async_session_maker() as session:
        projects = (await session.execute(select(Project.id))).scalars().all()
        users = (await session.execute(select(User.id))).scalars().all()
        if len(projects) == 1:
            project_id = projects[0]
            existing = set((await session.execute(select(ProjectMember.user_id).where(ProjectMember.project_id == project_id))).scalars())
            for user_id in users:
                if user_id not in existing:
                    session.add(ProjectMember(project_id=project_id, user_id=user_id))
            await session.commit()
    print("[OK] Database tables created/verified")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "EPC-Intel API"}
