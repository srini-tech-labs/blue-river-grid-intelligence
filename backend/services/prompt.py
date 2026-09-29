"""Grounded prompt assembly, ported from Stage 3 `20_hybrid_rag_generation`.

The asset-mode [S1] block, [D#] blocks, grounding rules and sections are kept
verbatim, except that the [D#] "Source URI" line is replaced by the file name
only, so internal storage paths are never sent to the model. Portfolio mode (no single asset) reuses the same rules with
portfolio-appropriate sections; see docs/stage3-port-notes.md.
"""

import json

from .knowledge import source_file

DOC_CONTENT_CHARS = 2200  # Stage 3 cap per document block


def _j(obj) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


def asset_structured_text(ctx: dict) -> str:
    asset = ctx["asset_summary"]
    return f"""
[S1] STRUCTURED OPERATIONAL DATA — BLUE RIVER POWER
Asset ID: {asset.get('asset_id')}
Substation: {asset.get('substation_id')}
Asset age (years): {asset.get('asset_age_years')}
Criticality: {asset.get('criticality')}
Average utilization (%): {asset.get('avg_utilization_pct')}
Maximum utilization (%): {asset.get('max_utilization_pct')}
Maximum top-oil temperature (C): {asset.get('max_top_oil_temp_c')}
Thermal alert count: {asset.get('thermal_alert_count')}
Outage count: {asset.get('outage_count')}
Outage minutes: {asset.get('outage_minutes')}
Customer interruptions: {asset.get('customer_interruptions')}
Last maintenance date: {asset.get('last_maintenance_date')}
Prototype risk score: {asset.get('risk_score')}
Prototype risk band: {asset.get('risk_band')}

IMPORTANT: The risk score is a transparent portfolio demonstration heuristic.
It is NOT a production engineering, protection, safety, or asset-health model.

Event timeline:
{_j(ctx.get('timeline', []))}

Work orders:
{_j(ctx.get('work_orders', []))}

Outages:
{_j(ctx.get('outages', []))}
""".strip()


def portfolio_structured_text(ctx: dict) -> str:
    return f"""
[S1] STRUCTURED OPERATIONAL DATA — BLUE RIVER POWER (PORTFOLIO)
Reliability KPIs (synthetic customer base): {_j(ctx.get('reliability', {}))}
Portfolio aggregates: {_j(ctx.get('portfolio', {}))}

Highest-priority assets by prototype risk score:
{_j(ctx.get('priority_assets', []))}

IMPORTANT: The risk score is a transparent portfolio demonstration heuristic.
It is NOT a production engineering, protection, safety, or asset-health model.

Maintenance summary:
{_j(ctx.get('maintenance', []))}
""".strip()


def documents_text(evidence: list[dict]) -> str:
    sections = []
    for item in evidence:
        sections.append(
            f"""
[{item['citation_label']}] DOCUMENT EVIDENCE
Document ID: {item.get('document_id')}
Type: {item.get('document_type')}
Title: {item.get('title')}
Date: {item.get('document_date')}
Asset: {item.get('asset_id')}
Work order: {item.get('work_order_id')}
Source file: {source_file(item.get('source_uri'))}
Content:
{(item.get('chunk_to_retrieve') or '')[:DOC_CONTENT_CHARS]}
""".strip()
        )
    return "\n\n".join(sections) if sections else "(No document evidence was retrieved.)"


_ASSET_SECTIONS = """- Executive Summary
- Structured Operational Evidence
- Historical and Document Evidence
- Corrective Maintenance Decision
- Policy / Procedure Context
- Remaining Uncertainty"""

_PORTFOLIO_SECTIONS = """- Executive Summary
- Structured Operational Evidence
- Document Evidence
- Policy / Procedure Context
- Remaining Uncertainty"""


def build_prompt(question: str, structured_text: str, docs_text: str, *, portfolio: bool) -> str:
    sections = _PORTFOLIO_SECTIONS if portfolio else _ASSET_SECTIONS
    return f"""
You are generating a grounded operational-intelligence answer for the synthetic
Blue River Power portfolio environment.

QUESTION:
{question}

Use ONLY the evidence supplied below. Do not use outside knowledge to invent
facts about this asset.

GROUNDING RULES:
1. Structured operational values must be supported with [S1].
2. Claims derived from documents must cite the matching [D#] label.
3. Do not cite a source unless it actually supports the statement.
4. If sources conflict, explicitly state the conflict and cite both sources.
5. Distinguish observations, historical indicators, corrective actions, and policy.
6. Do not describe the prototype risk score as a real engineering or safety model.
7. Do not claim that correlation proves causation.
8. If evidence is insufficient, say what cannot be concluded.
9. Keep the answer concise but technically useful.

Use these sections:
{sections}

STRUCTURED EVIDENCE:
{structured_text}

UNSTRUCTURED DOCUMENT EVIDENCE:
{docs_text}
""".strip()
