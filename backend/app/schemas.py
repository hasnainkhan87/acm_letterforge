from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class Party(BaseModel):
    name: str
    position: str
    organization: str

Style = Literal["very_short", "concise", "formal", "detailed"]

class GenerateIn(BaseModel):
    prompt: str
    style: Style = "concise"

class GenerateOut(BaseModel):
    subject: str
    body: str

class LetterIn(BaseModel):
    template_id: int
    sender: Party
    recipient: Party
    through: Optional[Party] = None
    subject: str
    body: str
    salutation: Literal["Respected Sir", "Respected Madam"] = "Respected Sir"
    font_name: Literal["Calibri", "Times New Roman", "Arial"] = "Calibri"
    font_size: int = Field(11, ge=9, le=16)
    signatory_ids: list[int] = Field(default_factory=list, max_length=3)

class LetterOut(LetterIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime
    description: Optional[str] = None
    signature_slots: int = 2
    default_left_role: Optional[str] = None
    default_right_role: Optional[str] = None

class SignatoryOut(Party):
    model_config = ConfigDict(from_attributes=True)
    id: int
    signature_path: Optional[str] = None
    sort_order: int

class ReorderIn(BaseModel):
    ids: list[int]


class ContactOut(Party):
    model_config = ConfigDict(from_attributes=True)
    id: int
