"""
Database seeder — creates sample data for all modules.
Run: python seed_db.py
"""
import asyncio
import json
from datetime import date, timedelta
from app.db.base import engine, Base
from app.modules.projects.models import Project
from app.modules.documents.models import Document, DocumentChunk
from app.modules.compliance.models import Specification, Submittal, Deviation, Vendor
from app.modules.rfi.models import Rfi
from app.modules.schedule.models import ScheduleTask, ScheduleRiskScore
from app.modules.supply_chain.models import Shipment, ShipmentEvent
from app.modules.commissioning.models import CommissioningTemplate, CommissioningRun, CommissioningStep
from app.modules.dashboard.models import Notification
from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.shared.ai.embedding_client import get_embedding


async def seed():
    print("🔄 Seeding database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    from app.db.base import async_session_maker

    async with async_session_maker() as session:
        # ── Users ──────────────────────────────────────────────
        admin = User(email="admin@epc-intel.com", password_hash=get_password_hash("admin"), name="EPC Admin", role="Admin")
        pm = User(email="pm@epc-intel.com", password_hash=get_password_hash("pm123"), name="Sarah Chen", role="PM")
        qa = User(email="qa@epc-intel.com", password_hash=get_password_hash("qa123"), name="James Miller", role="QA_ENGINEER")
        procurement = User(email="procurement@epc-intel.com", password_hash=get_password_hash("proc123"), name="David Park", role="PROCUREMENT")
        commissioning_eng = User(email="comm@epc-intel.com", password_hash=get_password_hash("comm123"), name="Ana Rivera", role="COMMISSIONING")
        session.add_all([admin, pm, qa, procurement, commissioning_eng])

        # ── Project ────────────────────────────────────────────
        project = Project(
            name="Hyperscale Data Center - Phase 1",
            location="Mumbai, India",
            client="TechCorp Global",
            start_date=date(2026, 1, 15),
            target_completion=date(2027, 6, 30),
            status="Active",
        )
        session.add(project)
        await session.flush()

        # ── Vendors ────────────────────────────────────────────
        vendor_a = Vendor(project_id=project.id, name="CoolSys International", category="HVAC")
        vendor_b = Vendor(project_id=project.id, name="PowerMax Solutions", category="Electrical")
        vendor_c = Vendor(project_id=project.id, name="SecureRack Inc", category="IT Infrastructure")
        session.add_all([vendor_a, vendor_b, vendor_c])
        await session.flush()

        # ── Documents ──────────────────────────────────────────
        spec_doc = Document(project_id=project.id, doc_type="specification", filename="HVAC_Cooling_Spec.pdf", storage_url="local://specs/hvac.pdf", ingestion_status="ready")
        sub_doc = Document(project_id=project.id, doc_type="submittal", filename="VendorA_Chiller_Submittal.pdf", storage_url="local://submittals/chiller.pdf", ingestion_status="ready")
        elec_doc = Document(project_id=project.id, doc_type="specification", filename="Electrical_Distribution_Spec.pdf", storage_url="local://specs/electrical.pdf", ingestion_status="ready")
        session.add_all([spec_doc, sub_doc, elec_doc])
        await session.flush()

        # ── Specifications ─────────────────────────────────────
        spec1 = Specification(project_id=project.id, document_id=spec_doc.id, spec_code="HVAC-01", section="4.2.1",
                              requirement_text="Chilled water supply temperature shall be maintained at 10°C +/- 1°C. Cooling capacity minimum 500kW.", numeric_requirement=500.0)
        spec2 = Specification(project_id=project.id, document_id=spec_doc.id, spec_code="HVAC-02", section="7.3",
                              requirement_text="Enclosure paint color must be bright white (#FFFFFF).", numeric_requirement=None)
        spec3 = Specification(project_id=project.id, document_id=elec_doc.id, spec_code="ELEC-01", section="3.1",
                              requirement_text="UPS system shall provide minimum 2N redundancy with battery autonomy of 15 minutes at full load.", numeric_requirement=15.0)
        spec4 = Specification(project_id=project.id, document_id=elec_doc.id, spec_code="ELEC-02", section="5.4",
                              requirement_text="Generator start time shall not exceed 10 seconds from mains failure detection.", numeric_requirement=10.0)
        session.add_all([spec1, spec2, spec3, spec4])
        await session.flush()

        # ── Document Chunks (with embeddings for RAG) ──────────
        chunks_data = [
            ("The HVAC cooling system is designed for a minimum load of 500kW. Chilled water supply must be 10°C. Clearances around the generator must be >= 900mm.", spec_doc.id, 4),
            ("Vendor A's proposed chiller unit provides 450kW capacity. It features a #F5F5F5 enclosure and uses R-134a refrigerant.", sub_doc.id, 12),
            ("UPS system architecture requires 2N redundancy configuration. Battery bank must support 15 minutes runtime at rated load.", elec_doc.id, 3),
            ("Generator specifications: Diesel-powered, 2000kVA rated capacity. Start time target 8 seconds. Fuel autonomy 48 hours.", elec_doc.id, 8),
            ("Cold aisle containment system: Temperature at rack inlet 18-27°C per ASHRAE A1. Hot aisle maximum 45°C.", spec_doc.id, 15),
        ]
        for text, doc_id, page in chunks_data:
            emb = get_embedding(text)
            chunk = DocumentChunk(document_id=doc_id, chunk_text=text, embedding=json.dumps(emb), page_number=page)
            session.add(chunk)

        # ── Submittals & Deviations ────────────────────────────
        sub1 = Submittal(project_id=project.id, document_id=sub_doc.id, vendor_id=vendor_a.id, status="under_review")
        session.add(sub1)
        await session.flush()

        dev1 = Deviation(submittal_id=sub1.id, spec_id=spec1.id,
                         description="Cooling capacity requirement not met. Spec requires 500kW, submittal provides 450kW.",
                         severity="Critical", detected_by="rule", status="open")
        dev2 = Deviation(submittal_id=sub1.id, spec_id=spec2.id,
                         description="Paint color specified as #FFFFFF, submittal proposes #F5F5F5.",
                         severity="Minor", detected_by="ai", status="open")
        session.add_all([dev1, dev2])

        # ── Schedule Tasks ─────────────────────────────────────
        today = date.today()
        tasks = [
            ScheduleTask(project_id=project.id, wbs_code="1.1", task_name="Site Preparation & Foundation",
                         planned_start=today - timedelta(days=90), planned_end=today - timedelta(days=30),
                         actual_start=today - timedelta(days=85), actual_end=today - timedelta(days=25),
                         duration_days=60, workforce_availability=95.0, status="completed"),
            ScheduleTask(project_id=project.id, wbs_code="1.2", task_name="Structural Steel Erection",
                         planned_start=today - timedelta(days=30), planned_end=today + timedelta(days=30),
                         actual_start=today - timedelta(days=25),
                         duration_days=60, workforce_availability=78.0, status="in_progress",
                         dependencies=json.dumps([])),
            ScheduleTask(project_id=project.id, wbs_code="2.1", task_name="Electrical Switchgear Installation",
                         planned_start=today + timedelta(days=10), planned_end=today + timedelta(days=50),
                         duration_days=40, workforce_availability=90.0, status="not_started"),
            ScheduleTask(project_id=project.id, wbs_code="2.2", task_name="UPS System Installation & Testing",
                         planned_start=today + timedelta(days=30), planned_end=today + timedelta(days=65),
                         duration_days=35, workforce_availability=85.0, status="not_started"),
            ScheduleTask(project_id=project.id, wbs_code="3.1", task_name="HVAC Chiller Plant Installation",
                         planned_start=today + timedelta(days=15), planned_end=today + timedelta(days=55),
                         duration_days=40, workforce_availability=60.0, status="not_started"),
            ScheduleTask(project_id=project.id, wbs_code="3.2", task_name="Raised Floor & Containment",
                         planned_start=today + timedelta(days=50), planned_end=today + timedelta(days=75),
                         duration_days=25, workforce_availability=92.0, status="not_started"),
            ScheduleTask(project_id=project.id, wbs_code="4.1", task_name="Fire Suppression System",
                         planned_start=today + timedelta(days=40), planned_end=today + timedelta(days=60),
                         duration_days=20, workforce_availability=100.0, status="not_started"),
            ScheduleTask(project_id=project.id, wbs_code="5.1", task_name="Commissioning & Handover",
                         planned_start=today + timedelta(days=75), planned_end=today + timedelta(days=100),
                         duration_days=25, workforce_availability=100.0, status="not_started"),
        ]
        session.add_all(tasks)
        await session.flush()

        # Set dependencies (after IDs are generated)
        tasks[2].dependencies = json.dumps([tasks[1].id])  # Switchgear depends on steel
        tasks[3].dependencies = json.dumps([tasks[2].id])  # UPS depends on switchgear
        tasks[4].dependencies = json.dumps([tasks[1].id])  # Chiller depends on steel
        tasks[5].dependencies = json.dumps([tasks[4].id, tasks[2].id])  # Raised floor depends on chiller + switchgear
        tasks[7].dependencies = json.dumps([tasks[3].id, tasks[5].id, tasks[6].id])  # Commissioning depends on all

        # Seed risk scores for tasks
        risk_scores = [
            ScheduleRiskScore(task_id=tasks[1].id, risk_score=62.5, predicted_delay_days=8,
                              contributing_factors=json.dumps(["Workforce shortage", "Schedule behind plan"])),
            ScheduleRiskScore(task_id=tasks[4].id, risk_score=78.3, predicted_delay_days=12,
                              contributing_factors=json.dumps(["Workforce shortage", "Vendor delivery risk", "Adverse weather forecast"])),
            ScheduleRiskScore(task_id=tasks[2].id, risk_score=45.0, predicted_delay_days=5,
                              contributing_factors=json.dumps(["Upstream dependency delayed"])),
        ]
        session.add_all(risk_scores)

        # ── Shipments ──────────────────────────────────────────
        ship1 = Shipment(project_id=project.id, vendor_id=vendor_b.id, equipment_type="UPS",
                         description="2MW UPS System - Liebert EXL S1",
                         origin_lat=35.6762, origin_lng=139.6503,  # Tokyo
                         destination_lat=19.0760, destination_lng=72.8777,  # Mumbai
                         required_on_site=today + timedelta(days=25), status="in_transit", risk_score=72.0)
        ship2 = Shipment(project_id=project.id, vendor_id=vendor_a.id, equipment_type="Chiller",
                         description="500kW Centrifugal Chiller Unit",
                         origin_lat=31.2304, origin_lng=121.4737,  # Shanghai
                         destination_lat=19.0760, destination_lng=72.8777,  # Mumbai
                         required_on_site=today + timedelta(days=15), status="at_risk", risk_score=85.0)
        ship3 = Shipment(project_id=project.id, vendor_id=vendor_b.id, equipment_type="Generator",
                         description="2000kVA Diesel Generator Set",
                         origin_lat=51.5074, origin_lng=-0.1278,  # London
                         destination_lat=19.0760, destination_lng=72.8777,  # Mumbai
                         required_on_site=today + timedelta(days=50), status="on_track", risk_score=18.0)
        ship4 = Shipment(project_id=project.id, vendor_id=vendor_b.id, equipment_type="Switchgear",
                         description="Medium Voltage Switchgear Panel",
                         origin_lat=48.8566, origin_lng=2.3522,  # Paris
                         destination_lat=19.0760, destination_lng=72.8777,  # Mumbai
                         required_on_site=today + timedelta(days=10), status="at_risk", risk_score=91.0)
        session.add_all([ship1, ship2, ship3, ship4])
        await session.flush()

        # Shipment events
        events = [
            ShipmentEvent(shipment_id=ship1.id, event_type="departed", lat=35.6762, lng=139.6503, notes="Departed Tokyo port"),
            ShipmentEvent(shipment_id=ship1.id, event_type="in_transit", lat=22.3193, lng=114.1694, notes="Passed Hong Kong"),
            ShipmentEvent(shipment_id=ship2.id, event_type="departed", lat=31.2304, lng=121.4737, notes="Departed Shanghai"),
            ShipmentEvent(shipment_id=ship2.id, event_type="delayed", lat=13.0827, lng=80.2707, notes="Customs delay at Chennai port"),
            ShipmentEvent(shipment_id=ship3.id, event_type="departed", lat=51.5074, lng=-0.1278, notes="Departed London"),
            ShipmentEvent(shipment_id=ship4.id, event_type="departed", lat=48.8566, lng=2.3522, notes="Departed Paris"),
            ShipmentEvent(shipment_id=ship4.id, event_type="delayed", lat=30.0444, lng=31.2357, notes="Held at Suez Canal - congestion"),
        ]
        session.add_all(events)

        # ── Commissioning Templates ───────────────────────────
        from app.modules.commissioning.templates import ALL_TEMPLATES
        for tmpl_data in ALL_TEMPLATES:
            tmpl = CommissioningTemplate(**tmpl_data)
            session.add(tmpl)

        # ── RFIs ──────────────────────────────────────────────
        rfi1 = Rfi(project_id=project.id, created_by=qa.id, subject="Generator Clearance Question",
                   question="What is the required clearance around the diesel generators on Level B1?", status="open")
        rfi2 = Rfi(project_id=project.id, created_by=pm.id, subject="UPS Battery Room Ventilation",
                   question="What ventilation rate is required for the UPS battery room per TIA-942?", status="open")
        session.add_all([rfi1, rfi2])

        # ── Notifications ─────────────────────────────────────
        notif1 = Notification(project_id=project.id, user_id=pm.id, type="deviation",
                              message="🚨 Critical deviation detected: Chiller capacity 450kW vs required 500kW",
                              related_entity_id=dev1.id)
        notif2 = Notification(project_id=project.id, user_id=pm.id, type="shipment_risk",
                              message="⚠️ Switchgear shipment at 91% risk — held at Suez Canal",
                              related_entity_id=ship4.id)
        notif3 = Notification(project_id=project.id, type="schedule_risk",
                              message="📊 HVAC Chiller Installation task at 78% delay risk — workforce at 60%",
                              related_entity_id=tasks[4].id)
        session.add_all([notif1, notif2, notif3])

        await session.commit()
        print("✅ Database successfully seeded with all module data.")
        print(f"   Project: {project.name}")
        print(f"   Users: admin@epc-intel.com / admin, pm@epc-intel.com / pm123")
        print(f"   Tasks: {len(tasks)} schedule tasks")
        print(f"   Shipments: 4 (2 at-risk)")
        print(f"   Templates: {len(ALL_TEMPLATES)} commissioning templates")


if __name__ == "__main__":
    asyncio.run(seed())
