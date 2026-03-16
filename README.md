python3 << 'EOF'
content = '''---
title: Semantic PII Detector
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# Semantic PII Detector

> Three-layer PII detection built for Indian enterprises.
> Catches what legacy tools miss — implied identity, contextual PHI, insider risk.

## Live Demo
- API docs: https://arryan-01-pii-detector.hf.space/docs
- Demo UI: https://pii-detector-hqdczbuqtnekjgmf2sg4j.streamlit.app

## What it detects

| Layer | Method | Catches |
|---|---|---|
| Layer 1 | Regex (Presidio) | Aadhaar, PAN, email, phone, IFSC, UPI, credit card |
| Layer 2 | Transformer NER (GLiNER) | Names, hospitals, diagnoses, companies, caste, DOB |
| Layer 3 | LLM (Groq/Llama) | Implied identity, insider risk, contextual PHI, business secrets |

## Benchmark (25 test cases — Indian enterprise context)

| Approach | Precision | Recall | F1 |
|---|---|---|---|
| Regex only (Layer 1) | 100% | 100% | 100% |
| NER only (Layer 2) | 71.4% | 100% | 83.3% |
| LLM only (Layer 3) | 90.9% | 100% | 95.2% |
| Full pipeline (all 3 layers) | 100% | 100% | 100% |

*Evaluated on 25 labeled test cases covering structured PII, named entities,
implied identity, insider risk, contextual PHI, and business secrets.*

## API endpoints

- POST /analyze — analyze plain text
- POST /analyze/upload — analyze uploaded file (pdf, docx, csv, json, html, eml, log)
- GET /health — health check

## Run locally
```bash
git clone https://github.com/arryan0112/pii-detector
cd pii-detector
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key" > .env
uvicorn app.main:app --reload
```

## Run with Docker
```bash
docker build -t pii-detector .
docker run -p 8000:8000 --env-file .env pii-detector
```

## Tech stack

- FastAPI + Pydantic
- Microsoft Presidio (custom Indian PII recognizers)
- GLiNER transformer (zero-shot NER)
- Groq API / Llama 3.3 70B (semantic reasoning)
- Streamlit (demo UI)
- Docker + HuggingFace Spaces
'''

with open('README.md', 'w') as f:
    f.write(content)

print("Done")

# Verify
with open('README.md', 'r') as f:
    lines = f.readlines()
print(f"Line 1: {lines[0].strip()!r}")
print(f"Line 2: {lines[1].strip()!r}")
print(f"Line 3: {lines[2].strip()!r}")
EOF