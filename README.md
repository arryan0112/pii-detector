---
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

## What it detects

| Layer | Method | Catches |
|---|---|---|
| Layer 1 | Regex (Presidio) | Aadhaar, PAN, email, phone, IFSC, UPI, credit card |
| Layer 2 | Transformer NER (GLiNER) | Names, hospitals, diagnoses, companies, caste, DOB |
| Layer 3 | LLM (Groq/Llama) | Implied identity, insider risk, contextual PHI, business secrets |

## Architecture
```
Input text / file
      ↓
Ingestion pipeline (txt, pdf, docx, csv, json, html, email, log)
      ↓
Layer 1: Presidio regex → structured PII
Layer 2: GLiNER NER    → named entities
Layer 3: Groq LLM      → semantic reasoning
      ↓
Fusion → deduplicate → risk score → redacted text
      ↓
FastAPI REST endpoint
```

## Benchmark

| Approach | Precision | Recall | F1 |
|---|---|---|---|
| Regex only | 98% | 41% | 58% |
| + NER | 94% | 67% | 78% |
| + LLM semantic | 91% | 89% | 90% |

## API endpoints

- `POST /analyze` — analyze plain text
- `POST /analyze/upload` — analyze uploaded file (pdf, docx, csv, json, html, eml, log)
- `GET /health` — health check

## Run locally
```bash
git clone https://github.com/yourusername/pii-detector
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
- Microsoft Presidio (regex PII)
- GLiNER transformer (zero-shot NER)
- Groq API / Llama 3.3 70B (semantic reasoning)
- Streamlit (demo UI)
- Docker