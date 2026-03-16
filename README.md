---
title: Semantic PII Detector
## Live Demo
- API docs: https://arryan-01-pii-detector.hf.space/docs
- Demo UI: https://pii-detector-hqdczb...streamlit.app
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

## Benchmark (25 test cases — Indian enterprise context)

| Approach | Precision | Recall | F1 |
|---|---|---|---|
| Regex only (Layer 1) | 100% | 100% | 100% |
| NER only (Layer 2) | 71.4% | 100% | 83.3% |
| LLM only (Layer 3) | 90.9% | 100% | 95.2% |
| Full pipeline (all 3 layers) | 100% | 100% | 100% |

*Evaluated on 25 labeled test cases covering structured PII, named entities, implied identity, insider risk, contextual PHI, and business secrets.*

## API endpoints

- POST /analyze — analyze plain text
- POST /analyze/upload — analyze uploaded file
- GET /health — health check

## Tech stack

- FastAPI + Pydantic
- Microsoft Presidio (regex PII)
- GLiNER transformer (zero-shot NER)
- Groq API / Llama 3.3 70B (semantic reasoning)
- Streamlit (demo UI)
- Docker
