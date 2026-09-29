"""Operations Intelligence: Delta facts [S1] + AI Search HYBRID evidence [D#]
-> grounded prompt -> ai_query(system.ai.gpt-oss-20b) -> answer + source manifest.

Context is rebuilt from live retrieval on every request.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor

from ..config import RISK_DISCLAIMER
from ..db import queries
from ..db.sql import run_query
from ..errors import ModelUnavailable
from . import asset_resolver, assets, knowledge, prompt, reliability
from .citations import citation_warnings, normalize_citations, validate_citations

log = logging.getLogger(__name__)

ASSET_DOC_RESULTS = 8
POLICY_DOC_RESULTS = 4
MAX_EVIDENCE = 10
MODEL_TIMEOUT_S = 150.0

_ID_LIKE_RE = re.compile(r"\b([A-Za-z]{2,5})-(\d{1,6})\b")


def _resolve(question: str, asset_id: str | None) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    mentioned = asset_resolver.find_in_question(question)

    known = asset_resolver.known_asset_ids()
    prefixes = {a.split("-")[0] for a in known}
    for prefix, num in _ID_LIKE_RE.findall(question):
        cand = f"{prefix.upper()}-{num}"
        if prefix.upper() in prefixes and cand not in known:
            warnings.append(f"{cand} is not an asset in the Blue River Power portfolio.")

    if asset_id:
        resolved = asset_resolver.validate(asset_id)
        others = [m for m in mentioned if m != resolved]
        if others:
            warnings.append(
                f"The question mentions {', '.join(others)}, but the selected asset context is {resolved}. "
                f"The answer is scoped to {resolved}."
            )
        return resolved, warnings

    if len(mentioned) == 1:
        return mentioned[0], warnings
    if len(mentioned) > 1:
        warnings.append(
            f"The question mentions several assets ({', '.join(mentioned)}). Answering at portfolio level; "
            "select a single asset for an asset-specific answer."
        )
    return None, warnings


def _structured(asset_id: str | None) -> dict:
    if asset_id:
        data = assets.get_asset_360(asset_id)
        return {
            "label": "S1",
            "scope": "asset",
            "asset_summary": data["asset_summary"],
            "timeline": data["timeline"],
            "work_orders": data["work_orders"],
            "outages": data["outages"],
        }
    ops = reliability.get_operations_summary()
    return {
        "label": "S1",
        "scope": "portfolio",
        "reliability": reliability.get_reliability_summary(),
        "portfolio": ops["portfolio"],
        "priority_assets": assets.get_high_risk_assets(10)["assets"],
        "maintenance": ops["maintenance"],
    }


def _retrieve_documents(question: str, asset_id: str | None) -> list[dict]:
    """Stage 3 pattern: scoped HYBRID search + separate POLICY search, dedupe, cap."""
    primary = knowledge.hybrid_search(
        question, {"asset_id": asset_id} if asset_id else None, ASSET_DOC_RESULTS
    )
    policy = knowledge.hybrid_search(question, {"document_type": "POLICY"}, POLICY_DOC_RESULTS)
    combined, seen = [], set()
    for row in primary + policy:
        key = row.get("chunk_id") or (row.get("document_id"), row.get("chunk_to_retrieve"))
        if key not in seen:
            seen.add(key)
            combined.append(row)
    evidence = combined[:MAX_EVIDENCE]
    for i, row in enumerate(evidence, start=1):
        row["citation_label"] = f"D{i}"
    return evidence


def _generate(prompt_text: str) -> str | None:
    rows = run_query(
        queries.AI_QUERY,
        {"prompt": prompt_text},
        timeout_s=MODEL_TIMEOUT_S,
        row_limit=1,
        failure_error=ModelUnavailable,
    )
    answer = rows[0]["answer"] if rows else None
    return str(answer).strip() if answer is not None else None


def ask_operations_intelligence(question: str, asset_id: str | None = None) -> dict:
    question = question.strip()
    resolved, warnings = _resolve(question, asset_id)

    # Search does not use the warehouse, so it can overlap the structured queries.
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_struct = pool.submit(_structured, resolved)
        f_docs = pool.submit(_retrieve_documents, question, resolved)
        structured = f_struct.result()
        evidence = f_docs.result()

    if not evidence:
        warnings.append("No document evidence was retrieved for this question; only structured data is available.")

    structured_text = (
        prompt.asset_structured_text(structured) if resolved else prompt.portfolio_structured_text(structured)
    )
    prompt_text = prompt.build_prompt(
        question, structured_text, prompt.documents_text(evidence), portfolio=resolved is None
    )
    log.info("operations_intelligence: scope=%s docs=%d prompt_chars=%d", resolved or "portfolio", len(evidence), len(prompt_text))

    answer = _generate(prompt_text)
    if answer:
        answer = normalize_citations(answer)
    valid = {e["citation_label"] for e in evidence}

    if not answer:
        check = validate_citations("", valid)
        warnings.append("The model did not return an answer. The available evidence is listed below.")
    else:
        check = validate_citations(answer, valid)
        warnings.extend(citation_warnings(check, len(evidence)))

    cited = set(check["document_labels_cited"])
    document_sources = [
        {"citation_label": e["citation_label"], "cited": e["citation_label"] in cited, **knowledge.to_source(e)}
        for e in evidence
    ]

    return {
        "answer": answer or "",
        "asset_id": resolved,
        "scope": "asset" if resolved else "portfolio",
        "structured_evidence": structured,
        "document_sources": document_sources,
        "citations": check,
        "warnings": warnings,
        "risk_disclaimer": RISK_DISCLAIMER,
        "synthetic": True,
    }
