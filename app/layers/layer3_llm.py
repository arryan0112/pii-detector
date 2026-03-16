import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.models import PIIFinding, DetectionSource

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY")
if not _api_key:
    print("WARNING: GROQ_API_KEY not set — Layer 3 will return empty findings")
else:
    print(f"GROQ_API_KEY loaded — first 8 chars: {_api_key[:8]}...")

_client = Groq(api_key=_api_key) if _api_key else None

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

DO NOT flag things regex already catches: emails, phone numbers, PAN, Aadhaar.
DO NOT flag generic statements not tied to any individual.

Return ONLY valid JSON, no explanation, no markdown, no code blocks:
{
  "findings": [
    {
      "text_span": "exact quote from input",
      "entity_type": "implied_identity|contextual_PHI|insider_risk|business_secret|sensitive_personal",
      "confidence": 0.95,
      "reasoning": "one sentence why this is sensitive"
    }
  ]
}

If nothing sensitive found, return exactly: {"findings": []}"""


def detect(text: str) -> list[PIIFinding]:
    if _client is None:
        print("  [Layer 3 skipped: no API key]")
        return []

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this text:\n\n{text}"}
            ],
            temperature=0.1,
            timeout=30
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
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

        print(f"  [Layer 3: found {len(findings)} findings]")
        return findings

    except json.JSONDecodeError as e:
        print(f"  [Layer 3 JSON error: {e}]")
        return []
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            print(f"  [Layer 3 skipped: rate limit — {error_msg[:100]}]")
        elif "401" in error_msg or "auth" in error_msg.lower():
            print(f"  [Layer 3 error: API key issue — {error_msg[:100]}]")
        else:
            print(f"  [Layer 3 error: {error_msg[:200]}]")
        return []