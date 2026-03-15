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