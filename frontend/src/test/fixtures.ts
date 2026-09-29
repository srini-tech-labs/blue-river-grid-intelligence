import type { Asset360, OperationsIntelligenceResponse } from '../api/types'

export const asset360: Asset360 = {
  asset_summary: {
    asset_id: 'TX-184', asset_type: 'POWER_TRANSFORMER', substation_id: 'SUB-07', criticality: 'HIGH',
    asset_age_years: 31, avg_utilization_pct: 65.99, max_utilization_pct: 97.26, max_top_oil_temp_c: 92.85,
    thermal_alert_count: 26, outage_count: 4, risk_score: 100, risk_band: 'HIGH',
  },
  timeline: [
    { event_date: '2022-08-18', event_type: 'CONDITION_FINDING', severity: 'MEDIUM', component: 'COOLING_SYSTEM', description: 'Minor airflow degradation.' },
  ],
  work_orders: [
    { work_order_id: 'WO-2841', created_date: '2026-06-15', completed_date: '2026-07-02', priority: 'P1', work_type: 'CORRECTIVE',
      component: 'COOLING_SYSTEM', status: 'COMPLETED', estimated_cost: 10000, actual_cost: 12000, summary: 'Replace fan bank.' },
  ],
  outages: [],
  risk_disclaimer: 'The risk score is a transparent portfolio demonstration heuristic.',
}

export const analysis: OperationsIntelligenceResponse = {
  answer: '## Executive Summary\nTX-184 is high priority [S1]. Cooling degraded [D1]. Policy applies [D2]. Invented [D7].',
  asset_id: 'TX-184',
  scope: 'asset',
  structured_evidence: { label: 'S1', scope: 'asset', asset_summary: asset360.asset_summary, timeline: [], work_orders: [], outages: [] },
  document_sources: [
    { citation_label: 'D1', cited: true, chunk_id: 'c1', document_id: 'INS-1', document_type: 'INSPECTION_REPORT',
      title: 'Field Inspection Report — TX-184', asset_id: 'TX-184', work_order_id: 'WO-2841', document_date: '2026-06-14',
      source_file: 'INS-1.pdf', content: 'Cooling fan bank degraded.' },
    { citation_label: 'D2', cited: true, chunk_id: 'c2', document_id: 'POL-1', document_type: 'POLICY',
      title: 'Thermal escalation policy', asset_id: null, work_order_id: null, document_date: '2025-01-01',
      source_file: 'POL-1.pdf', content: 'Escalate repeated alerts.' },
    { citation_label: 'D3', cited: false, chunk_id: 'c3', document_id: 'EM-1', document_type: 'EMAIL_THREAD',
      title: 'Email thread', asset_id: 'TX-184', work_order_id: null, document_date: '2026-06-12',
      source_file: null, content: 'Follow-up.' },
  ],
  citations: { structured_cited: true, document_labels_cited: ['D1', 'D2'], unknown_labels: ['D7'], substantive: true },
  warnings: ['The answer references citation labels that do not match any retrieved source ([D7]); those references are unverified.'],
  risk_disclaimer: 'The risk score is a transparent portfolio demonstration heuristic.',
}
