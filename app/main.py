import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze, health

app = FastAPI(
    title="Semantic PII Detector",
    description="""
    Three-layer PII detection built for Indian enterprises.

    Layer 1 — Regex (Presidio): emails, phones, Aadhaar, PAN, IFSC, UPI
    Layer 2 — Transformer NER (GLiNER): names, organizations, medical conditions
    Layer 3 — LLM (Groq/Llama): implied identity, insider risk, contextual PHI
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, tags=["analyze"])

@app.on_event("startup")
async def startup_check():
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("WARNING: GROQ_API_KEY not set — Layer 3 will not work")
    else:
        print(f"GROQ_API_KEY loaded — first 8 chars: {groq_key[:8]}...")