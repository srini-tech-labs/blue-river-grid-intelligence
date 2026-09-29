export interface Reliability {
  saidi: number | null
  saifi: number | null
  caidi: number | null
  customer_base: number | null
  period: string | null
  as_of_date: string | null
  outage_events?: number
  customer_interruptions?: number
  customer_interruption_minutes?: number
  synthetic: boolean
}

export interface AssetSummary {
  asset_id: string
  asset_type?: string
  substation_id: string
  manufacturer?: string
  install_date?: string
  asset_age_years: number
  rated_mva?: number
  primary_kv?: number
  secondary_kv?: number
  criticality: string
  status?: string
  avg_utilization_pct: number
  max_utilization_pct: number
  avg_top_oil_temp_c?: number
  max_top_oil_temp_c: number
  thermal_alert_count: number
  outage_count: number
  outage_minutes?: number
  customer_interruptions?: number
  total_mw_interrupted?: number
  work_order_count?: number
  last_maintenance_date?: string | null
  maintenance_cost?: number
  risk_score: number
  risk_band: string
}

export interface PriorityAssets {
  assets: AssetSummary[]
  disclaimer: string
}

export interface TimelineEvent {
  record_id?: string
  event_date: string
  event_type: string
  severity: string
  component: string
  description: string
}

export interface WorkOrder {
  work_order_id: string
  created_date: string
  completed_date: string | null
  priority: string
  work_type: string
  component: string
  status: string
  estimated_cost: number | null
  actual_cost: number | null
  summary: string
}

export interface Outage {
  outage_id: string
  start_ts: string
  end_ts: string | null
  duration_minutes: number | null
  customers_affected: number | null
  mw_interrupted: number | null
  cause_category: string
  reportable: boolean | null
}

export interface Asset360 {
  asset_summary: AssetSummary
  timeline: TimelineEvent[]
  work_orders: WorkOrder[]
  outages: Outage[]
  risk_disclaimer: string
}

export interface MaintenanceRow {
  component: string
  work_type: string
  priority: string
  work_order_count: number
  actual_cost: number
  avg_days_to_complete: number
}

export interface OperationsSummary {
  portfolio: {
    asset_count?: number
    high_band_assets?: number
    high_criticality_assets?: number
    thermal_alerts?: number
    asset_outages?: number
    outage_minutes?: number
    work_orders?: number
    maintenance_cost?: number
  }
  maintenance: MaintenanceRow[]
}

export interface DocumentSource {
  chunk_id: string | null
  document_id: string | null
  document_type: string | null
  title: string | null
  asset_id: string | null
  work_order_id: string | null
  document_date: string | null
  /** File name only; storage locations are never sent to the browser. */
  source_file: string | null
  content: string | null
}

export interface KnowledgeSearchResponse {
  results: DocumentSource[]
}

export interface CitedSource extends DocumentSource {
  citation_label: string
  cited: boolean
}

export interface StructuredEvidence {
  label: 'S1'
  scope: 'asset' | 'portfolio'
  asset_summary?: AssetSummary
  timeline?: TimelineEvent[]
  work_orders?: WorkOrder[]
  outages?: Outage[]
  reliability?: Reliability
  portfolio?: OperationsSummary['portfolio']
  priority_assets?: AssetSummary[]
  maintenance?: MaintenanceRow[]
}

export interface OperationsIntelligenceResponse {
  answer: string
  asset_id: string | null
  scope: 'asset' | 'portfolio'
  structured_evidence: StructuredEvidence
  document_sources: CitedSource[]
  citations: {
    structured_cited: boolean
    document_labels_cited: string[]
    unknown_labels: string[]
    substantive: boolean
  }
  warnings: string[]
  risk_disclaimer: string
}
