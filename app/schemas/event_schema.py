from typing import Any, Optional
from pydantic import BaseModel


class JobEvent(BaseModel):
    event_id: int
    job_id: str
    item_id: Optional[str] = None
    type: str
    level: str = "info"
    message: str
    data: Any = None
    created_at: str
