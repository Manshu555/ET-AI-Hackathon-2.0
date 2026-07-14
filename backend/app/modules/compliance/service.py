from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.compliance.models import Submittal, Deviation, Specification
from app.modules.documents.models import DocumentChunk, Document
from app.shared.ai.embedding_client import get_embedding
from app.core.config import settings
import json
import re
import logging

logger = logging.getLogger(__name__)

from app.modules.compliance.numeric_rules import extract_numeric_value

async def run_compliance_check(db: AsyncSession, submittal_id: str):
    # 1. Fetch Submittal and its chunks
    result = await db.execute(select(Submittal).where(Submittal.id == submittal_id))
    submittal = result.scalars().first()
    
    if not submittal:
        raise ValueError("Submittal not found")
        
    sub_chunks_result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == submittal.document_id)
    )
    submittal_chunks = sub_chunks_result.scalars().all()
    
    # 2. Retrieve Specifications for this project
    spec_result = await db.execute(select(Specification).where(Specification.project_id == submittal.project_id))
    specs = spec_result.scalars().all()
    
    # Check each submittal chunk against specs
    for chunk in submittal_chunks:
        for spec in specs:
            # Deterministic numeric check
            if spec.numeric_requirement is not None:
                extracted_val = extract_numeric_value(chunk.chunk_text)
                if extracted_val and extracted_val < spec.numeric_requirement:
                    dev = Deviation(
                        submittal_id=submittal.id,
                        spec_id=spec.id,
                        description=f"Value {extracted_val} does not meet requirement {spec.numeric_requirement}",
                        severity="Major",
                        detected_by="rule"
                    )
                    db.add(dev)
                    continue
            
            # AI Check using new google.genai SDK
            if settings.GEMINI_API_KEY:
                try:
                    from google import genai
                    
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    prompt = f"""You are a compliance agent reviewing a submittal against a specification.
Specification: {spec.requirement_text}
Submittal Text: {chunk.chunk_text}

Does the submittal deviate from the specification? If so, reply with JSON: {{"deviates": true, "severity": "Minor|Major|Critical", "description": "..."}}. 
If it complies, reply with {{"deviates": false}}."""
                    
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    response_text = response.text
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        if parsed.get("deviates"):
                            dev = Deviation(
                                submittal_id=submittal.id,
                                spec_id=spec.id,
                                description=parsed.get("description", "AI detected deviation"),
                                severity=parsed.get("severity", "Major"),
                                detected_by="ai"
                            )
                            db.add(dev)
                except Exception as e:
                    logger.error(f"LLM Error during compliance check: {e}")
                    
    await db.commit()
