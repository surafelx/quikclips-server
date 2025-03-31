from pydantic import BaseModel
from typing import Optional

class ClippingRequest(BaseModel):
    min_duration: int
    max_duration: int
    num_clips: int
    suggestion_prompt: Optional[str] = None
