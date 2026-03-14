import re
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from app.models import PIIFinding, DetectionSource


# ── Custom Indian + universal recognizers ────────────────────────────────────

# PAN card: 5 uppercase letters, 4 digits, 1 uppercase letter
# Example: ABCDE1234F
pan_recognizer = PatternRecognizer(
    supported_entity="IN_PAN",
    patterns=[Pattern(
        name="pan_pattern",
        regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        score=0.9
    )],
    context=["pan", "permanent account", "income tax", "tax"]
)

# Aadhaar: 12 digits, optionally grouped in sets of 4
# Example: 2345 6789 0123 or 234567890123
aadhaar_recognizer = PatternRecognizer(
    supported_entity="IN_AADHAAR",
    patterns=[
        Pattern(
            name="aadhaar_spaced",
            regex=r"\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b",
            score=0.9
        ),
        Pattern(
            name="aadhaar_plain",
            regex=r"\b[2-9]{1}[0-9]{11}\b",
            score=0.6  # lower score — 12 digits alone could be anything
        ),
    ],
    context=["aadhaar", "aadhar", "uid", "uidai", "biometric"]
)

# Indian phone numbers: +91 followed by 10 digits (various formats)
# Examples: +91 98765 43210, +919876543210, 09876543210
india_phone_recognizer = PatternRecognizer(
    supported_entity="IN_PHONE",
    patterns=[
        Pattern(
            name="india_phone_intl",
            regex=r"\+91[\s\-]?[6-9][0-9]{9}\b",
            score=0.95
        ),
        Pattern(
            name="india_phone_zero",
            regex=r"\b0[6-9][0-9]{9}\b",
            score=0.85
        ),
        Pattern(
            name="india_phone_bare",
            regex=r"\b[6-9][0-9]{9}\b",
            score=0.6  # lower — 10 digits starting 6-9, could be other numbers
        ),
    ],
    context=["call", "phone", "mobile", "contact", "whatsapp", "number"]
)

# Credit/debit cards: 16 digits optionally grouped by 4
# Example: 4532-1234-5678-9012 or 4532123456789012
card_recognizer = PatternRecognizer(
    supported_entity="CREDIT_CARD",
    patterns=[
        Pattern(
            name="card_dashes",
            regex=r"\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b",
            score=0.95
        ),
    ],
    context=["card", "credit", "debit", "payment", "visa", "mastercard"]
)

# Indian passport: starts with letter, 7 digits
# Example: A1234567
passport_recognizer = PatternRecognizer(
    supported_entity="IN_PASSPORT",
    patterns=[Pattern(
        name="passport_pattern",
        regex=r"\b[A-PR-WY][1-9]\d{7}\b",
        score=0.75
    )],
    context=["passport", "travel", "visa"]
)

# Indian vehicle registration: state code + district + series + number
# Example: MH 12 AB 1234 or KA01AB1234
vehicle_recognizer = PatternRecognizer(
    supported_entity="IN_VEHICLE",
    patterns=[Pattern(
        name="vehicle_pattern",
        regex=r"\b[A-Z]{2}[\s\-]?[0-9]{2}[\s\-]?[A-Z]{1,2}[\s\-]?[0-9]{4}\b",
        score=0.8
    )],
    context=["vehicle", "car", "bike", "registration", "rc", "number plate"]
)

# Indian IFSC code: bank branch identifier
# Example: HDFC0001234
ifsc_recognizer = PatternRecognizer(
    supported_entity="IN_IFSC",
    patterns=[Pattern(
        name="ifsc_pattern",
        regex=r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
        score=0.85
    )],
    context=["ifsc", "bank", "transfer", "neft", "rtgs", "imps", "account"]
)

# UPI ID: user@bankhandle
# Example: priya@okicici, 9876543210@paytm
upi_recognizer = PatternRecognizer(
    supported_entity="IN_UPI",
    patterns=[Pattern(
        name="upi_pattern",
        regex=r"\b[\w.\-]{3,}@(?:okicici|oksbi|okaxis|okhdfcbank|paytm|ybl|ibl|axl|upi|apl|rajgovhdfcbank|waicici)\b",
        score=0.95
    )],
    context=["upi", "pay", "payment", "gpay", "phonepe", "paytm"]
)


# ── Build engine with all recognizers ────────────────────────────────────────

def _build_engine() -> AnalyzerEngine:
    engine = AnalyzerEngine()
    engine.registry.add_recognizer(pan_recognizer)
    engine.registry.add_recognizer(aadhaar_recognizer)
    engine.registry.add_recognizer(india_phone_recognizer)
    engine.registry.add_recognizer(card_recognizer)
    engine.registry.add_recognizer(passport_recognizer)
    engine.registry.add_recognizer(vehicle_recognizer)
    engine.registry.add_recognizer(ifsc_recognizer)
    engine.registry.add_recognizer(upi_recognizer)
    return engine

_engine = _build_engine()

ENTITY_TYPES = [
    # Universal
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "PERSON",
    "LOCATION",
    # Indian-specific (our custom recognizers)
    "IN_PAN",
    "IN_AADHAAR",
    "IN_PHONE",
    "CREDIT_CARD",
    "IN_PASSPORT",
    "IN_VEHICLE",
    "IN_IFSC",
    "IN_UPI",
]


def detect(text: str) -> list[PIIFinding]:
    results = _engine.analyze(text=text, entities=ENTITY_TYPES, language="en")

    findings = []
    seen_spans = set()  # deduplicate overlapping detections

    for r in sorted(results, key=lambda x: x.score, reverse=True):
        span_key = (r.start, r.end)
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)

        findings.append(PIIFinding(
            text_span=text[r.start:r.end],
            entity_type=r.entity_type,
            source=DetectionSource.REGEX,
            confidence=round(r.score, 3),
            start_char=r.start,
            end_char=r.end
        ))

    return findings