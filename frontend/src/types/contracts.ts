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

export interface RootCauseCandidate {
  label: string;
  score: number;
  supporting_return_count: number;
  top_terms: string[];
}

export interface RootCauseOutput {
  product: string;
  issue: string;
  candidates: RootCauseCandidate[];
  top_candidate: string;
  confidence: number;
  product_id?: string | null;
  supplier_id?: string | null;
  model_name: string;
  model_version: string;
  is_emerging_spike: boolean;
  abuse_risk: number;
  notes: string[];
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
