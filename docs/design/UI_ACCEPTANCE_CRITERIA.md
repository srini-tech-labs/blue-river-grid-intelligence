# Blue River Grid Intelligence — UI Acceptance Criteria

## Global

The application must:

- display the name **Blue River Grid Intelligence**
- identify Blue River Power as synthetic/demo data
- work as one Databricks App
- have no credentials in browser code
- use a professional operations-oriented visual design
- remain usable on a laptop during screen sharing
- provide clear loading and error states

## Reliability Command Center

Must show:

- SAIDI
- SAIFI
- CAIDI
- synthetic customer base / period where useful
- Priority Assets list/table
- risk/priority disclaimer
- operational summary
- clickable navigation to Asset 360

TX-184 should be easy to find, but the view must be data-driven.

## Asset 360

Must show:

- asset identity
- substation
- criticality
- age
- utilization
- temperature/thermal alert metrics
- outage metrics
- risk heuristic with disclaimer
- timeline
- work orders
- outages
- document/evidence access
- button/action to open Operations Intelligence scoped to the asset

## Operations Intelligence

Must show:

- question input
- optional/current asset context
- useful example prompts
- generated answer
- clear loading state
- structured evidence indicator
- document source list/evidence drawer
- warning/disclaimer area
- graceful no-answer/insufficient-evidence state

The UI should not render raw JSON or force the user to interpret `[D1]` labels without a human-readable source panel.

## Evidence UX

For each cited document, show where available:

- title
- document type
- document date
- asset
- work order
- short evidence excerpt

The app should make it easy to see which evidence supports the model response.

## Error UX

The app should give clear non-technical messages for:

- SQL warehouse temporarily unavailable
- AI Search unavailable
- model temporarily unavailable
- unknown asset
- no evidence found

Do not expose stack traces.

## Demo acceptance

Before public packaging, demonstrate:

1. Command Center loads.
2. TX-184 opens in Asset 360.
3. Timeline/work orders/outages load.
4. Knowledge search returns real indexed evidence.
5. Operations Intelligence answers the flagship TX-184 question.
6. Operations Intelligence displays structured and document evidence.
7. No credentials or internal workspace URLs appear in the UI.
8. Risk score disclaimer is visible.
9. Synthetic environment labeling is visible.
