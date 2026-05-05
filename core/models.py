from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional

class LeadData(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_time: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "new"
    consent_given: bool = False
    parent_full_name: Optional[str] = None        
    parent_phone: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    value: Optional[str] = None
    error_message: Optional[str] = None