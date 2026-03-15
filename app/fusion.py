from app.models import PIIFinding, AnalysisResult, DetectionSource
from app.layers import layer1_regex as l1
from app.layers import layer2_ner as l2
from app.layers import layer3_llm as l3


def _spans_overlap(a: PIIFinding, b: PIIFinding) -> bool:
    """Check if two findings refer to the same text span."""
    if all(x is not None for x in [a.start_char, a.end_char, b.start_char, b.end_char]):
        return not (a.end_char <= b.start_char or b.end_char <= a.start_char)
    a_text = a.text_span.lower().strip()
    b_text = b.text_span.lower().strip()
    return a_text in b_text or b_text in a_text


def _deduplicate(findings: list[PIIFinding]) -> list[PIIFinding]:
    """Keep the best detection when multiple layers find the same span."""
    sorted_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)
    kept = []
    for candidate in sorted_findings:
        already_covered = any(_spans_overlap(candidate, k) for k in kept)
        if not already_covered:
            kept.append(candidate)
    return kept


def _filter_noise(findings: list[PIIFinding]) -> list[PIIFinding]:
    """Remove low-value findings that add noise."""
    noise_words = {"age", "the", "a", "an", "is", "was", "date", "name"}
    filtered = []
    for f in findings:
        if len(f.text_span.strip()) <= 2:
            continue
        if f.text_span.lower().strip() in noise_words:
            continue
        filtered.append(f)
    return filtered


def _compute_risk_score(findings: list[PIIFinding]) -> float:
    """
    Risk score 0-10.
    LLM findings weighted highest — they catch the most dangerous cases.
    NER findings medium — named entities are sensitive but well understood.
    Regex findings lowest — structured PII is important but routine.
    """
    weights = {
        DetectionSource.REGEX: 1.0,
        DetectionSource.NER:   1.5,
        DetectionSource.LLM:   3.0,
    }
    raw = sum(weights[f.source] * f.confidence for f in findings)
    return round(min(raw, 10.0), 2)


def _redact(text: str, findings: list[PIIFinding]) -> str:
    """Replace sensitive spans with [ENTITY_TYPE] placeholders."""
    # Positional findings (regex + NER) — replace by char position end to start
    positional = [f for f in findings if f.start_char is not None]
    positional.sort(key=lambda f: f.start_char, reverse=True)

    result = text
    for f in positional:
        result = result[:f.start_char] + f"[{f.entity_type}]" + result[f.end_char:]

    # LLM findings — replace by string match
    for f in findings:
        if f.start_char is None and f.text_span in result:
            result = result.replace(f.text_span, f"[{f.entity_type}]")

    return result


def analyze(text: str, run_llm: bool = True) -> AnalysisResult:
    """
    Run all three detection layers and merge results.
    
    run_llm=False skips the LLM layer — useful for large document
    chunks where you want to save Groq quota.
    """
    layer1_findings = l1.detect(text)
    layer2_findings = l2.detect(text)
    layer3_findings = l3.detect(text) if run_llm else []

    all_findings = layer1_findings + layer2_findings + layer3_findings
    all_findings = _filter_noise(all_findings)
    unique_findings = _deduplicate(all_findings)
    unique_findings.sort(key=lambda f: f.confidence, reverse=True)

    breakdown = {
        "regex": sum(1 for f in unique_findings if f.source == DetectionSource.REGEX),
        "ner":   sum(1 for f in unique_findings if f.source == DetectionSource.NER),
        "llm":   sum(1 for f in unique_findings if f.source == DetectionSource.LLM),
    }

    return AnalysisResult(
        original_text=text,
        findings=unique_findings,
        risk_score=_compute_risk_score(unique_findings),
        redacted_text=_redact(text, unique_findings),
        layer_breakdown=breakdown
    )


def analyze_document(chunks: list, max_llm_chunks: int = 5) -> dict:
    """
    Analyze a multi-chunk document from the ingestion pipeline.
    
    Only runs the LLM layer on the first max_llm_chunks chunks
    to stay within Groq free tier limits.
    All chunks get layers 1 and 2.
    
    Returns a combined result across all chunks.
    """
    all_findings = []
    errors = []
    llm_chunks_used = 0

    for i, chunk in enumerate(chunks):
        # Run LLM only on first max_llm_chunks chunks
        use_llm = llm_chunks_used < max_llm_chunks

        try:
            result = analyze(chunk.text, run_llm=use_llm)
            if use_llm:
                llm_chunks_used += 1

            # Tag each finding with its source location in the document
            for f in result.findings:
                f_dict = f.model_dump()
                f_dict["document_location"] = chunk.location
                all_findings.append(f_dict)

        except Exception as e:
            errors.append(f"Chunk {i} ({chunk.location}): {e}")

    # Compute overall risk score from all findings
    total_risk = min(
        sum(
            (3.0 if f["source"] == "llm" else 1.5 if f["source"] == "ner" else 1.0)
            * f["confidence"]
            for f in all_findings
        ),
        10.0
    )

    return {
        "total_chunks": len(chunks),
        "llm_analyzed_chunks": llm_chunks_used,
        "total_findings": len(all_findings),
        "risk_score": round(total_risk, 2),
        "findings": all_findings,
        "errors": errors,
        "layer_breakdown": {
            "regex": sum(1 for f in all_findings if f["source"] == "regex"),
            "ner":   sum(1 for f in all_findings if f["source"] == "ner"),
            "llm":   sum(1 for f in all_findings if f["source"] == "llm"),
        }
    }