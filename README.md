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

## Benchmark

| Approach | Precision | Recall | F1 |
|---|---|---|---|
| Regex only | 98% | 41% | 58% |
| + NER | 94% | 67% | 78% |
| + LLM semantic | 91% | 89% | 90% |

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
