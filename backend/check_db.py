import asyncio
from sqlalchemy import select, desc
import json
from app.db.base import async_session_maker
from app.modules.schedule.models import ScheduleRiskScore, ScheduleTask

async def run():
    async with async_session_maker() as db:
        try:
            risk_query = select(ScheduleRiskScore).order_by(desc(ScheduleRiskScore.risk_score)).limit(5)
            risk_res = await db.execute(risk_query)
            risk_scores = risk_res.scalars().all()
            
            schedule_risk = []
            for rs in risk_scores:
                task_res = await db.execute(select(ScheduleTask).where(ScheduleTask.id == rs.task_id))
                task = task_res.scalars().first()
                
                schedule_risk.append({
                    "task_id": rs.task_id,
                    "task_name": task.task_name if task else "Unknown",
                    "wbs_code": task.wbs_code if task else None,
                    "risk_score": rs.risk_score,
                    "predicted_delay_days": rs.predicted_delay_days,
                    "contributing_factors": json.loads(rs.contributing_factors) if rs.contributing_factors else [],
                    "status": task.status if task else "not_started",
                })
            print("SUCCESS:", schedule_risk)
        except Exception as e:
            print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(run())
