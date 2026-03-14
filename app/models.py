from pydantic import BaseModel
from enum import Enum
from typing import Optional

class DetectionSource(str, Enum):
    REGEX = "regex"
    NER   = "ner"
    LLM   = "llm"

class PIIFinding(BaseModel):
    text_span:   str
    entity_type: str
    source:      DetectionSource
    confidence:  float
    reasoning:   Optional[str] = None
    start_char:  Optional[int] = None
    end_char:    Optional[int] = None

class AnalysisResult(BaseModel):
    original_text:   str
    findings:        list[PIIFinding]
    risk_score:      float
    redacted_text:   str
    layer_breakdown: dict

class AnalyzeRequest(BaseModel):
    text: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Patient in room 11 with rare condition. Contact john@corp.com"
            }
        }
    }