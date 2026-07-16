from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.documents.search import find_similar_chunks
import json
import logging
import uuid
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


async def check_compliance(
    db: AsyncIOMotorDatabase,
    submittal_id: str,
    spec_id: str,
    project_id: str,
) -> dict:
    from openai import OpenAI

    submittal = await db.submittals.find_one({"_id": submittal_id})
    if not submittal:
        return {"error": "Submittal not found"}
        
    spec = await db.specifications.find_one({"_id": spec_id})
    if not spec:
        return {"error": "Specification not found"}

    search_query = f"{spec['title']} {spec['content']} {submittal['title']}"
    search_results = await find_similar_chunks(db, search_query, project_id=project_id, top_k=3)

    context_texts = [sr.chunk['chunk_text'] for sr in search_results]
    context_block = "\n".join(context_texts)

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set in environment.")
        return {"error": "Missing OpenRouter API Key"}

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        prompt = f"""You are a compliance checker for an engineering project.
Compare the submittal against the specification and relevant document context.
Determine if the submittal complies with the specification.
If it deviates, provide a severity (Minor, Major, Critical) and a description.

Specification: {spec['title']} - {spec['content']}
Submittal: {submittal['title']} - {submittal['description']}
Context: {context_block}

Return a JSON object in this format exactly:
{{"deviates": true, "severity": "Major", "description": "Reason for deviation"}}
If it complies, reply with {{"deviates": false}}."""
        
        response = client.chat.completions.create(
            model="google/gemini-3.5-flash",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.choices[0].message.content
        
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        
        result = json.loads(response_text)
        
        if result.get("deviates"):
            deviation = {
                "_id": str(uuid.uuid4()),
                "submittal_id": submittal_id,
                "spec_id": spec_id,
                "description": result.get("description", "Unknown deviation"),
                "severity": result.get("severity", "Minor"),
                "detected_by": "ai",
                "status": "open",
                "created_at": datetime.utcnow()
            }
            await db.deviations.insert_one(deviation)
            deviation["id"] = deviation.pop("_id")
            return {"status": "deviated", "deviation": deviation}
        else:
            return {"status": "compliant"}

    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        return {"error": str(e)}
