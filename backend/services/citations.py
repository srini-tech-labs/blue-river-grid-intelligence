"""Citation validation against the retrieved evidence manifest (Stage 3 checks)."""

import re

_DOC_LABEL_RE = re.compile(r"\[(D\d+)\]")

_LABEL = r"(?:S1|D\d+)"
_GROUP_RE = re.compile(rf"[\[(]\s*({_LABEL}(?:\s*[,;]\s*{_LABEL})+)\s*[\])]")
_PAREN_RE = re.compile(rf"\(\s*({_LABEL})\s*\)")


def normalize_citations(answer: str) -> str:
    """Rewrite common model variants -- "(D3)", "(S1)", "[D1, D3]", "(D1; D2)" --
    to the canonical "[D#]"/"[S1]" form used by the Stage 3 checks and the UI."""
    answer = _GROUP_RE.sub(lambda m: "".join(f"[{x.strip()}]" for x in re.split(r"[,;]", m.group(1))), answer)
    return _PAREN_RE.sub(r"[\1]", answer)


def validate_citations(answer: str, valid_doc_labels: set[str]) -> dict:
    used = set(_DOC_LABEL_RE.findall(answer or ""))
    unknown = used - valid_doc_labels
    return {
        "structured_cited": "[S1]" in (answer or ""),
        "document_labels_cited": sorted(used & valid_doc_labels, key=lambda s: int(s[1:])),
        "unknown_labels": sorted(unknown, key=lambda s: int(s[1:])),
        "substantive": len((answer or "").strip()) >= 300,
    }


def citation_warnings(check: dict, docs_available: int) -> list[str]:
    warnings = []
    if not check["structured_cited"]:
        warnings.append("The answer does not cite the structured operational evidence [S1].")
    if docs_available >= 2 and len(check["document_labels_cited"]) < 2:
        warnings.append("The answer cites fewer than two retrieved documents; treat document-based claims with caution.")
    if check["unknown_labels"]:
        labels = ", ".join(f"[{x}]" for x in check["unknown_labels"])
        warnings.append(f"The answer references citation labels that do not match any retrieved source ({labels}); those references are unverified.")
    if not check["substantive"]:
        warnings.append("The generated answer is unusually short; the evidence may be insufficient.")
    return warnings
