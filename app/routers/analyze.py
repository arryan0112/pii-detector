from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models import AnalyzeRequest, AnalysisResult
from app.fusion import analyze, analyze_document
from app.ingestion.pipeline import ingest_bytes, ingest_text

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_text(req: AnalyzeRequest):
    """
    Analyze plain text for PII.
    Runs all three layers: regex, NER, LLM semantic reasoning.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if len(req.text) > 10_000:
        raise HTTPException(status_code=400, detail="Text too long — max 10,000 chars")

    try:
        return analyze(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/upload")
async def analyze_file(file: UploadFile = File(...)):
    """
    Analyze an uploaded file for PII.
    Supports: txt, pdf, docx, csv, json, html, eml, log
    Ingests the file, chunks it, runs detection on each chunk.
    LLM layer runs on first 5 chunks only to stay within Groq free tier.
    """
    allowed = {".txt", ".pdf", ".docx", ".csv", ".json",
               ".html", ".htm", ".eml", ".log", ".jsonl"}

    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed)}"
        )

    try:
        raw = await file.read()
        if len(raw) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File too large — max 5MB")

        ingestion_result = ingest_bytes(raw, file.filename or "upload")

        if not ingestion_result.chunks:
            raise HTTPException(
                status_code=422,
                detail=f"No text could be extracted. Errors: {ingestion_result.errors}"
            )

        result = analyze_document(
            ingestion_result.chunks,
            max_llm_chunks=5
        )

        return {
            "filename": file.filename,
            "format": ingestion_result.format,
            "total_chars": ingestion_result.total_chars,
            "ingestion_errors": ingestion_result.errors,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))