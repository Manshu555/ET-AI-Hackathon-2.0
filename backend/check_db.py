import asyncio
import traceback
from sqlalchemy import select
from app.db.base import async_session_maker
from app.modules.documents.models import Document

async def run():
    async with async_session_maker() as db:
        try:
            print("--- Testing list documents ---")
            result = await db.execute(select(Document))
            docs = result.scalars().all()
            print(f"OK: Found {len(docs)} documents")
            for d in docs[:3]:
                print(f"  - {d.filename} | project_id={d.project_id} | status={d.ingestion_status}")
        except Exception as e:
            print("ERROR on list:", e)
            traceback.print_exc()

        try:
            print("\n--- Testing insert document ---")
            from app.modules.projects.models import Project
            proj_res = await db.execute(select(Project).limit(1))
            proj = proj_res.scalars().first()
            print(f"Project found: {proj.id if proj else None}")
        except Exception as e:
            print("ERROR on project query:", e)
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
