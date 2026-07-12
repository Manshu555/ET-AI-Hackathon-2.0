import asyncio
import json
from app.db.base import engine, Base
from app.modules.projects.models import Project
from app.modules.documents.models import Document, DocumentChunk
from app.modules.compliance.models import Specification, Submittal, Deviation
from app.modules.rfi.models import Rfi
from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.shared.ai.embedding_client import get_embedding

async def seed():
    print("Seeding database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    from app.db.base import async_session_maker
    
    async with async_session_maker() as session:
        # Create user
        user = User(
            email="admin@epc-intel.com",
            password_hash=get_password_hash("admin"),
            name="EPC Admin",
            role="Admin"
        )
        session.add(user)
        
        # Create Project
        project = Project(
            name="Hyperscale Data Center - Phase 1",
            location="Mumbai, India",
            status="Active"
        )
        session.add(project)
        await session.flush()
        
        # Create Spec Document
        spec_doc = Document(
            project_id=project.id,
            doc_type="specification",
            filename="HVAC_Cooling_Spec.pdf",
            storage_url="local://specs/hvac.pdf",
            ingestion_status="ready"
        )
        session.add(spec_doc)
        await session.flush()
        
        # Create Submittal Document
        sub_doc = Document(
            project_id=project.id,
            doc_type="submittal",
            filename="VendorA_Chiller_Submittal.pdf",
            storage_url="local://submittals/chiller.pdf",
            ingestion_status="ready"
        )
        session.add(sub_doc)
        await session.flush()
        
        # Create Vendor
        from app.modules.compliance.models import Vendor
        vendor = Vendor(
            project_id=project.id,
            name="Vendor A Cooling Systems",
            category="HVAC"
        )
        session.add(vendor)
        await session.flush()
        
        # Create Spec
        spec = Specification(
            project_id=project.id,
            document_id=spec_doc.id,
            spec_code="HVAC-01",
            section="4.2.1",
            requirement_text="Chilled water supply temperature shall be maintained at 10°C +/- 1°C. Cooling capacity minimum 500kW.",
            numeric_requirement=500.0
        )
        session.add(spec)
        await session.flush()
        
        spec2 = Specification(
            project_id=project.id,
            document_id=spec_doc.id,
            spec_code="HVAC-02",
            section="7.3",
            requirement_text="Enclosure paint color must be bright white (#FFFFFF).",
            numeric_requirement=None
        )
        session.add(spec2)
        await session.flush()
        
        # Create chunks for RFI search
        chunk1_text = "The HVAC cooling system is designed for a minimum load of 500kW. Chilled water supply must be 10C. Clearances around the generator must be >= 900mm."
        chunk1_emb = get_embedding(chunk1_text)
        
        chunk2_text = "Vendor A's proposed chiller unit provides 450kW capacity. It features a #F5F5F5 enclosure and uses R-134a refrigerant."
        chunk2_emb = get_embedding(chunk2_text)
        
        c1 = DocumentChunk(
            document_id=spec_doc.id,
            chunk_text=chunk1_text,
            embedding=json.dumps(chunk1_emb),
            page_number=4
        )
        c2 = DocumentChunk(
            document_id=sub_doc.id,
            chunk_text=chunk2_text,
            embedding=json.dumps(chunk2_emb),
            page_number=12
        )
        session.add(c1)
        session.add(c2)
        
        # Create Submittal Record
        sub = Submittal(
            project_id=project.id,
            document_id=sub_doc.id,
            vendor_id=vendor.id,
            status="pending"
        )
        session.add(sub)
        await session.flush()
        
        # Create Deviations
        dev1 = Deviation(
            submittal_id=sub.id,
            spec_id=spec.id,
            description="Cooling capacity requirement not met. Spec requires 500kW, submittal provides 450kW.",
            severity="Critical",
            detected_by="rule"
        )
        dev2 = Deviation(
            submittal_id=sub.id,
            spec_id=spec2.id,
            description="Paint color specified as #FFFFFF, submittal proposes #F5F5F5.",
            severity="Minor",
            detected_by="ai"
        )
        session.add(dev1)
        session.add(dev2)
        
        # Create RFI
        rfi = Rfi(
            project_id=project.id,
            created_by=user.id,
            subject="Generator Clearance Question",
            question="What is the required generator clearance?",
            status="open"
        )
        session.add(rfi)
        
        await session.commit()
        print("Database successfully seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
