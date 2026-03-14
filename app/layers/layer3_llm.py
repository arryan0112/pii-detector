import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from app.models import PIIFinding, DetectionSource

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are a data security analyst for Indian enterprises.
Your job is to find sensitive information that regex and NER models CANNOT detect.

Focus ONLY on these categories that pattern matching misses:
- implied_identity: describes a specific person without naming them
  Example: "the only female engineer on the team who resigned last week"
- contextual_PHI: medical info tied to someone through context
  Example: "the patient in bed 4 with the rare blood disorder"
- insider_risk: behavioral signals suggesting data theft or misuse
  Example: "before I leave next week I will copy the client database"
- business_secret: unreleased financials, strategy, or confidential plans
  Example: "we are acquiring XYZ company next quarter before announcement"
- sensitive_personal: caste, religion, political views tied to a person
  Example: "the Dalit employee in accounts was denied the promotion"

DO NOT flag things that regex already catches: emails, phone numbers, PAN, Aadhaar.
DO NOT flag generic statements not tied to any individual.

Return ONLY valid JSON, no explanation, no markdown, no code blocks:
{
  "findings": [
    {
      "text_span": "exact quote from input",
      "entity_type": "implied_identity|contextual_PHI|insider_risk|business_secret|sensitive_personal",
      "confidence": 0.0,
      "reasoning": "one sentence why this is sensitive"
    }
  ]
}

If nothing sensitive found, return exactly: {"findings": []}"""


def detect(text: str) -> list[PIIFinding]:
    prompt = f"{SYSTEM_PROMPT}\n\nAnalyze this text:\n\n{text}"

    try:
        response = _model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        findings = []

        for f in data.get("findings", []):
            findings.append(PIIFinding(
                text_span=f["text_span"],
                entity_type=f["entity_type"],
                source=DetectionSource.LLM,
                confidence=float(f["confidence"]),
                reasoning=f.get("reasoning")
            ))
        return findings

    except json.JSONDecodeError:
        # Gemini occasionally returns malformed JSON — fail silently
        return []
    except Exception:
        return []