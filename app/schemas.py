from pydantic import BaseModel
from typing import Optional

class EmailIn(BaseModel):
    uid: str
    sender: str
    subject: str
    body_text: str

class PredictionOut(BaseModel):
    email_uid: str
    spam_score: float
    spam_label: bool
    category_label: str
    category_confidence: float
    routed_folder: str
    routed_action: str

class FeedbackIn(BaseModel):
    email_uid: str
    old_label: str
    corrected_label: str
    note: Optional[str] = None