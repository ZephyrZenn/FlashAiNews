"""Memory router for viewing historical summary memories."""

from fastapi import APIRouter, HTTPException
from apps.backend.models.common import success_with_data
from core.db.pool import get_connection

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{memory_id}")
async def get_memory(memory_id: int):
    """获取历史记忆详情"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, topic, reasoning, content, created_at
                   FROM summary_memories
                   WHERE id = %s""",
                (memory_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return success_with_data({
                "id": row[0],
                "topic": row[1],
                "reasoning": row[2],
                "content": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            })
