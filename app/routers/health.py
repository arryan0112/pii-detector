from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "layers": ["regex", "ner", "llm"],
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile"
    }