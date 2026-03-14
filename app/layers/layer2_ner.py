from gliner import GLiNER
from app.models import PIIFinding, DetectionSource

_model = GLiNER.from_pretrained("knowledgator/gliner-multitask-large-v0.5")

SENSITIVE_LABELS = [
    "person name",
    "patient name",
    "employee name",
    "doctor name",
    "organization name",
    "hospital name",
    "company name",
    "home address",
    "medical condition",
    "diagnosis",
    "patient ID",
    "employee ID",
    "salary information",
    "bank account number",
    "date of birth",
    "age",
    "religion",
    "caste",
    "political affiliation",
]

def detect(text: str) -> list[PIIFinding]:
    entities = _model.predict_entities(
        text,
        SENSITIVE_LABELS,
        threshold=0.35
    )

    findings = []
    for e in entities:
        findings.append(PIIFinding(
            text_span=e["text"],
            entity_type=e["label"],
            source=DetectionSource.NER,
            confidence=round(e["score"], 3),
            start_char=e["start"],
            end_char=e["end"]
        ))
    return findings