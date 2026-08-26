# app/schemas/common.py
from pydantic import BaseModel
from typing import Any, Dict, Optional

class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int