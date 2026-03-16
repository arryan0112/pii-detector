import streamlit as st
import httpx

API_URL = "https://arryan-01-pii-detector.hf.space"

st.set_page_config(
    page_title="Semantic PII Detector",
    page_icon="🔍",
    layout="wide"
)

st.title("Semantic PII Detector")
st.caption("Three-layer detection for Indian enterprises — Regex + Transformer NER + LLM semantic reasoning")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Try an example")
    examples = {
        "Structured PII": "My PAN card is ABCDE1234F and Aadhaar is 2345 6789 0123. Email: priya@company.in, Phone: +91 98765 43210",
        "Medical + Named": "Dr. Rajesh Kumar from Apollo Hospital diagnosed Priya Sharma with Type 2 Diabetes. Contact: priya@gmail.com",
        "Insider risk": "Before I leave next month I will move the entire client database to my personal Google Drive.",
        "Implied identity": "The only female engineer on the Bangalore team who resigned last Tuesday took the source code with her.",
        "Sensitive personal": "The Dalit employee in the accounts department was passed over for promotion again this year.",
        "Mixed — high risk": """Dr. Rajesh Kumar diagnosed Priya Sharma with HIV.
Her Aadhaar is 2345 6789 0123, PAN is ABCDE1234F.
Before I leave next month I will copy the client list to my personal drive.
Contact: priya@gmail.com, +91 98765 43210""",
    }
    choice = st.selectbox("Select example", list(examples.keys()))
    if st.button("Load example", use_container_width=True):
        st.session_state["input_text"] = examples[choice]

    st.divider()
    st.markdown("**How it works**")
    st.markdown("- 🟢 **Regex** — Aadhaar, PAN, phone, email, IFSC, UPI")
    st.markdown("- 🔵 **NER** — names, hospitals, diagnoses, companies")
    st.markdown("- 🔴 **LLM** — implied identity, insider risk, contextual PHI")

# ── Source colors ─────────────────────────────────────────────────────────────

SOURCE_COLORS = {
    "regex": "#1D9E75",   # green
    "ner":   "#534AB7",   # purple
    "llm":   "#D85A30",   # coral/red
}

SOURCE_LABELS = {
    "regex": "REGEX",
    "ner":   "NER",
    "llm":   "LLM",
}

# ── Main input ────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Analyze text", "Upload file"])

with tab1:
    text_input = st.text_area(
        "Paste text to analyze",
        value=st.session_state.get("input_text", ""),
        height=150,
        placeholder="Paste any text containing potential PII..."
    )

    if st.button("Analyze text", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Running all three detection layers..."):
                try:
                    response = httpx.post(
                        f"{API_URL}/analyze",
                        json={"text": text_input},
                        timeout=60
                    )
                    response.raise_for_status()
                    st.session_state["result"] = response.json()
                    st.session_state["mode"] = "text"
                except httpx.HTTPStatusError as e:
                    st.error(f"API error {e.response.status_code}: {e.response.text}")
                except Exception as e:
                    st.error(f"Could not connect to API: {e}")

with tab2:
    uploaded = st.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "docx", "csv", "json", "html", "eml", "log"],
        help="Max 5MB. LLM layer runs on first 5 chunks to stay within free tier limits."
    )

    if st.button("Analyze file", type="primary", use_container_width=True):
        if uploaded is None:
            st.warning("Please upload a file first.")
        else:
            with st.spinner(f"Ingesting and analyzing {uploaded.name}..."):
                try:
                    response = httpx.post(
                        f"{API_URL}/analyze/upload",
                        files={"file": (uploaded.name, uploaded.read(), uploaded.type)},
                        timeout=120
                    )
                    response.raise_for_status()
                    st.session_state["result"] = response.json()
                    st.session_state["mode"] = "file"
                except httpx.HTTPStatusError as e:
                    st.error(f"API error {e.response.status_code}: {e.response.text}")
                except Exception as e:
                    st.error(f"Could not connect to API: {e}")

# ── Results ───────────────────────────────────────────────────────────────────

if "result" in st.session_state:
    result = st.session_state["result"]
    mode   = st.session_state.get("mode", "text")

    st.divider()

    # Metric cards
    findings = result.get("findings", [])
    breakdown = result.get("layer_breakdown", {})
    risk = result.get("risk_score", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Risk score", f"{risk} / 10",
                delta="HIGH" if risk >= 7 else "MEDIUM" if risk >= 4 else "LOW",
                delta_color="inverse")
    col2.metric("Total findings", len(findings))
    col3.metric("Regex", breakdown.get("regex", 0))
    col4.metric("NER", breakdown.get("ner", 0))
    col5.metric("LLM semantic", breakdown.get("llm", 0))

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Findings")
        if not findings:
            st.success("No PII detected.")
        else:
            for f in findings:
                color = SOURCE_COLORS.get(f["source"], "#888")
                label = SOURCE_LABELS.get(f["source"], f["source"].upper())
                confidence_pct = int(f["confidence"] * 100)

                st.markdown(
                    f'<div style="border-left: 3px solid {color}; padding: 8px 12px; '
                    f'margin-bottom: 8px; border-radius: 0 6px 6px 0; '
                    f'background: var(--background-color)">'
                    f'<span style="background:{color}; color:white; font-size:11px; '
                    f'padding:2px 6px; border-radius:3px; font-weight:600">{label}</span>'
                    f'&nbsp;&nbsp;<strong>{f["entity_type"]}</strong>'
                    f'&nbsp;<span style="color:gray; font-size:12px">({confidence_pct}%)</span><br>'
                    f'<code style="font-size:13px">{f["text_span"]}</code>'
                    + (f'<br><span style="font-size:12px; color:gray">{f["reasoning"]}</span>'
                       if f.get("reasoning") else "")
                    + '</div>',
                    unsafe_allow_html=True
                )

            if mode == "file":
                st.caption(f"Document location shown per finding above")

    with col_right:
        st.subheader("Redacted text")
        redacted = result.get("redacted_text", "")
        st.code(redacted, language=None)

        if mode == "file":
            st.subheader("File info")
            st.json({
                "filename": result.get("filename"),
                "format": result.get("format"),
                "total_chars": result.get("total_chars"),
                "total_chunks": result.get("total_chunks"),
                "llm_analyzed_chunks": result.get("llm_analyzed_chunks"),
                "ingestion_errors": result.get("ingestion_errors", [])
            })