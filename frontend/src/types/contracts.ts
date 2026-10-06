/**
 * Shared Multi-Agent Retail System TypeScript Contracts
 * Conforming strictly to `shared/retail_common/schemas/` & `shared/retail_common/taxonomy.py`
 */

export const CONTRACT_VERSION = '1.1';

// ── Taxonomy Reference ────────────────────────────────────────────────────────
export type RootCause =
  | 'manufacturing_defect'
  | 'damaged_in_transit'
  | 'wrong_item_shipped'
  | 'size_fit_issue'
  | 'not_as_described'
  | 'quality_durability'
  | 'late_delivery'
  | 'change_of_mind'
  | 'policy_abuse_suspected'
  | 'unknown';

export type Decision = 'approve' | 'reject' | 'escalate' | 'request_info';

export type Intent = 'return' | 'exchange' | 'refund' | 'complaint' | 'unknown';

export type Sentiment = 'positive' | 'neutral' | 'negative';

export interface Entity {
  type: string;
  text: string;
  start?: number | null;
  end?: number | null;
}

export interface IntakeOutput {
  raw_text: string;
  product: string;
  issue: string;
  intent: string;
  sentiment: string;
  confidence: number;
  return_id: string;
  tenant_id: string;
  clean_text: string;
  summary: string;
  product_id?: string | null;
  product_match_score: number;
  entities: Entity[];
  lang: string;
  pii_types_found: string[];
  flags: string[];
}

// ── Agent 2 - Root Cause MCP Schemas ───────────────────────────────────────────
export interface RootCauseCandidate {
  label: string;
  score: number;
  supporting_return_count?: number;
  top_terms?: string[];
}

export interface RootCauseOutput {
  product: string;
  issue: string;
  candidates: RootCauseCandidate[];
  top_candidate: string;
  confidence: number;
  product_id?: string | null;
  supplier_id?: string | null;
  model_name?: string;
  model_version?: string;
  is_emerging_spike?: boolean;
  abuse_risk?: number;
  notes?: string[];
}

export interface EvidenceItem {
  source_type: string;
  source_id: string;
  snippet: string;
  relevance_score: number;
  title: string;
  method: string;
  matched_terms: string[];
  zone: string;
  label_hint?: string | null;
  metadata: Record<string, string>;
}

export interface EvidenceOutput {
  query: string;
  evidence: EvidenceItem[];
  total_results: number;
  corrected_query: string;
  expanded_terms: string[];
  method: string;
  latency_ms: number;
}

export interface AgentStep {
  agent: string;
  tool: string;
  ok: boolean;
  latency_ms: number;
  note: string;
}

export interface DecisionOutput {
  root_cause: string;
  confidence: number;
  evidence_summary: string;
  recommendation: string;
  requires_human_review: boolean;
  return_id: string;
  decision: string;
  citations: string[];
  reasoning_steps: string[];
  human_review_reasons: string[];
  risk_flags: string[];
  agent_trace: AgentStep[];
  evidence_support: number;
  disclaimer: string;
}

// ── Bulk Processing Schemas (`shared/retail_common/schemas/bulk.py`) ───────────
export interface BulkRow {
  return_id: string;
  text: string;
  order_id?: string | null;
  product_id?: string | null;
  customer_ref?: string | null;
  order_value_lkr?: number | null;
  purchase_date?: string | null;
  return_date?: string | null;
  store_id?: string | null;
  courier?: string | null;
}

export interface RowError {
  row: number;
  field: string;
  reason: string;
}

export interface BulkJob {
  job_id: string;
  name?: string;
  created_at?: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  total: number;
  processed: number;
  failed: number;
  errors: RowError[];
}

export interface Finding {
  kind:
    | 'root_cause'
    | 'product'
    | 'supplier'
    | 'batch'
    | 'cluster'
    | 'spike'
    | string;
  title: string;
  detail: string;
  return_count: number;
  value_at_risk_lkr: number;
  p_value?: number | null;
  product_id?: string | null;
  supplier_id?: string | null;
  batch_id?: string | null;
}

export interface IssueCluster {
  cluster_id: number;
  size: number;
  top_terms: string[];
  dominant_root_cause: string;
  growth_vs_prev?: number | null;
}

export interface BulkSummary {
  job_id: string;
  total: number;
  decisions: Record<string, number>;
  by_root_cause: Record<string, number>;
  findings: Finding[];
  clusters: IssueCluster[];
  needs_review: number;
  est_value_at_risk_lkr: number;
  executive_summary: string;
}

export interface ProductImpactItem {
  product_id: string;
  product_name: string;
  category: string;
  return_count: number;
  avg_order_value_lkr: number;
  value_at_risk_lkr: number;
  top_root_cause: string;
  top_root_cause_share: number;
  is_emerging_spike: boolean;
}

export interface WeeklyTrendPoint {
  week: string;
  counts: Record<string, number>;
  total?: number;
}

export interface BatchInvestigationItem {
  batch_id: string;
  supplier_id: string;
  supplier_name: string;
  mfg_date: string;
  units_shipped: number;
  units_returned: number;
  defect_rate: number;
  p_value: number;
  is_suspicious: boolean;
  primary_cause: string;
  notes: string;
}

export interface ProductRootCauseReport {
  product_id: string;
  product_name: string;
  category: string;
  avg_order_value_lkr: number;
  window_days: number;
  total_returns: number;
  total_units_sold: number;
  overall_return_rate: number;
  label_distribution: Record<string, number>;
  weekly_trend: WeeklyTrendPoint[];
  suppliers: Finding[];
  batches: BatchInvestigationItem[];
  headline: string;
  recommended_actions: string[];
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export type UserRole = 'viewer' | 'reviewer' | 'admin';

export interface AuthUser {
  sub: string;
  tenant_id: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// ── Usage / Metering ──────────────────────────────────────────────────────────
export interface UsageResponse {
  tenant_id: string;
  month: string;
  tier: string;
  usage: {
    return_processed: number;
    bulk_row: number;
    api_call: number;
    llm_tokens: number;
    total_returns: number;
  };
  plan_limits: {
    included_returns: number;
    included_api_calls: number;
  };
  estimated_invoice_lkr: number;
}

// ── Bulk Job API Response ─────────────────────────────────────────────────────
export interface BulkJobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  processed_rows: number;
  failed_rows: number;
  summary?: {
    total_processed: number;
    failed: number;
    executive_summary: string;
  } | null;
}

export interface BulkResultRow {
  return_id: string;
  decision: string;
  root_cause: string;
  confidence: number;
  recommendation: string;
}

export interface BulkResultsResponse {
  job_id: string;
  page: number;
  size: number;
  results: BulkResultRow[];
}
