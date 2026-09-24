import React, { useState } from 'react';
import { DecisionOutput } from '@/types/contracts';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ChevronDown,
  ShieldAlert,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { submitReview } from '@/lib/api';

// ── Decision Badge ────────────────────────────────────────────────────────────
function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<
    string,
    { icon: React.ReactNode; cls: string; label: string }
  > = {
    approve: {
      icon: <CheckCircle className="h-3 w-3 text-emerald-600" />,
      cls: 'border-emerald-200 bg-emerald-50 text-emerald-800',
      label: 'Approved',
    },
    reject: {
      icon: <XCircle className="h-3 w-3 text-rose-600" />,
      cls: 'border-rose-200 bg-rose-50 text-rose-800',
      label: 'Rejected',
    },
    escalate: {
      icon: <AlertTriangle className="h-3 w-3 text-amber-600" />,
      cls: 'border-amber-200 bg-amber-50 text-amber-800',
      label: 'Escalated',
    },
    request_info: {
      icon: <HelpCircle className="h-3 w-3 text-sky-600" />,
      cls: 'border-sky-200 bg-sky-50 text-sky-800',
      label: 'More Info Needed',
    },
  };
  const config = map[decision] ?? {
    icon: <HelpCircle className="h-3 w-3 text-neutral-500" />,
    cls: 'border-neutral-200 bg-neutral-100 text-neutral-700',
    label: decision,
  };
  return (
    <Badge
      variant="outline"
      className={`flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-xs font-medium ${config.cls}`}
    >
      {config.icon}
      {config.label}
    </Badge>
  );
}

// ── Review Panel ──────────────────────────────────────────────────────────────
function ReviewPanel({
  returnId,
  userRole,
}: {
  returnId: string;
  userRole: string;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverride, setShowOverride] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  if (!['reviewer', 'admin'].includes(userRole)) return null;

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      await submitReview(returnId, 'confirm');
      setDone('Decision confirmed.');
    } catch {
      setDone('Error submitting review.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverride = async () => {
    if (!overrideReason.trim()) return;
    setSubmitting(true);
    try {
      await submitReview(returnId, 'override', overrideReason);
      setDone('Decision overridden.');
    } catch {
      setDone('Error submitting override.');
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
        <CheckCircle className="h-3.5 w-3.5" />
        {done}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Button
          id="review-confirm"
          size="sm"
          disabled={submitting}
          onClick={handleConfirm}
          className="h-8 rounded-full bg-black px-4 text-xs text-white hover:bg-neutral-800"
        >
          {submitting ? (
            <Spinner className="h-3 w-3 text-white" />
          ) : (
            'Confirm Decision'
          )}
        </Button>
        <Button
          id="review-override-toggle"
          size="sm"
          variant="outline"
          onClick={() => setShowOverride((v) => !v)}
          className="h-8 rounded-full border-neutral-200 px-4 text-xs text-neutral-700 hover:bg-neutral-100"
        >
          Override…
        </Button>
      </div>

      {showOverride && (
        <div className="space-y-2">
          <Textarea
            id="override-reason"
            placeholder="Required: enter your reason for overriding this decision…"
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            className="min-h-[80px] resize-none rounded-lg border-neutral-200 text-xs"
          />
          <Button
            id="review-override-submit"
            size="sm"
            disabled={submitting || !overrideReason.trim()}
            onClick={handleOverride}
            className="h-8 rounded-full bg-rose-600 px-4 text-xs text-white hover:bg-rose-700"
          >
            {submitting ? (
              <Spinner className="h-3 w-3 text-white" />
            ) : (
              'Submit Override'
            )}
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Main DecisionCard ─────────────────────────────────────────────────────────
interface DecisionCardProps {
  result: DecisionOutput;
  userRole?: string;
}

export function DecisionCard({
  result,
  userRole = 'viewer',
}: DecisionCardProps) {
  const [traceOpen, setTraceOpen] = useState(false);
  const confidencePct = Math.round(result.confidence * 100);

  return (
    <div className="space-y-4">
      {/* ── Header row ── */}
      <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
        <CardHeader className="p-5 pb-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-sm font-semibold text-neutral-950">
                Decision Result
              </CardTitle>
              <CardDescription className="mt-0.5 font-mono text-xs text-neutral-400">
                {result.return_id}
              </CardDescription>
            </div>
            <DecisionBadge decision={result.decision} />
          </div>
        </CardHeader>
        <CardContent className="space-y-4 p-5 pt-0">
          {/* Confidence */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-500">Confidence</span>
              <span className="font-mono text-xs font-medium text-neutral-900">
                {confidencePct}% likelihood, not a guarantee
              </span>
            </div>
            <Progress value={confidencePct} className="h-1.5" />
          </div>

          {/* Root Cause + Evidence Support */}
          <div className="flex flex-wrap gap-2">
            <Badge
              variant="outline"
              className="rounded-full border-neutral-200 bg-neutral-100 font-mono text-[11px] text-neutral-700"
            >
              Root cause: {result.root_cause.replace(/_/g, ' ')}
            </Badge>
            <Badge
              variant="outline"
              className="rounded-full border-neutral-200 bg-neutral-100 font-mono text-[11px] text-neutral-700"
            >
              Evidence support: {Math.round(result.evidence_support * 100)}%
            </Badge>
          </div>

          {/* Summary */}
          <p className="text-sm leading-relaxed text-neutral-600">
            {result.evidence_summary || result.recommendation}
          </p>

          {/* Disclaimer — always visible */}
          <div className="rounded-lg border border-amber-100 bg-amber-50/60 px-3 py-2 text-[11px] text-amber-800">
            <ShieldAlert className="mr-1.5 inline h-3 w-3" />
            {result.disclaimer ||
              'AI-generated analysis. This output is probabilistic and must be reviewed by a qualified human before any binding retail decision is made.'}
          </div>
        </CardContent>
      </Card>

      {/* ── Risk Flags ── */}
      {result.risk_flags?.length > 0 && (
        <Card className="rounded-xl border border-rose-200 bg-rose-50/30 shadow-none">
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-rose-600" />
              <span className="text-xs font-semibold text-rose-800">
                Risk Flags
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.risk_flags.map((flag, i) => (
                <Badge
                  key={i}
                  variant="outline"
                  className="rounded-full border-rose-200 bg-white font-mono text-[10px] text-rose-700"
                >
                  {flag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Evidence List ── */}
      {result.citations?.length > 0 && (
        <Card className="rounded-xl border border-neutral-200 shadow-none">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-700">
              Evidence Citations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 p-5 pt-0">
            {result.citations.map((cit, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2"
              >
                <span className="font-mono text-xs text-neutral-700">
                  {cit}
                </span>
                <ExternalLink className="h-3 w-3 text-neutral-400" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── Reasoning Timeline ── */}
      {result.reasoning_steps?.length > 0 && (
        <Card className="rounded-xl border border-neutral-200 shadow-none">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-700">
              Reasoning Steps
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="relative space-y-3 pl-5">
              <div className="absolute bottom-1 left-1.5 top-1 w-px bg-neutral-200" />
              {result.reasoning_steps.map((step, i) => (
                <div key={i} className="relative flex items-start gap-3">
                  <span className="absolute -left-4 mt-1 flex h-3 w-3 items-center justify-center rounded-full bg-neutral-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-neutral-600" />
                  </span>
                  <p className="text-xs leading-relaxed text-neutral-600">
                    {step}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Agent Trace (Collapsible) ── */}
      {result.agent_trace?.length > 0 && (
        <Collapsible open={traceOpen} onOpenChange={setTraceOpen}>
          <Card className="rounded-xl border border-neutral-200 shadow-none">
            <CollapsibleTrigger asChild>
              <CardHeader className="cursor-pointer select-none p-5 pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-700">
                    Agent Trace Latencies
                  </CardTitle>
                  <ChevronDown
                    className={`h-4 w-4 text-neutral-400 transition-transform ${traceOpen ? 'rotate-180' : ''}`}
                  />
                </div>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="space-y-2 p-5 pt-0">
                {result.agent_trace.map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2"
                  >
                    <div className="space-y-0.5">
                      <p className="text-xs font-medium text-neutral-800">
                        {step.agent}
                      </p>
                      <p className="font-mono text-[10px] text-neutral-400">
                        {step.tool}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {step.ok ? (
                        <CheckCircle className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <XCircle className="h-3 w-3 text-rose-500" />
                      )}
                      <span className="flex items-center gap-1 font-mono text-[11px] text-neutral-500">
                        <Clock className="h-3 w-3" />
                        {step.latency_ms}ms
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      )}

      {/* ── Human Review Panel ── */}
      {result.requires_human_review && (
        <Card className="rounded-xl border border-amber-200 bg-amber-50/30 shadow-none">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-amber-800">
              Human Review Required
            </CardTitle>
            {result.human_review_reasons?.length > 0 && (
              <ul className="mt-1 space-y-0.5">
                {result.human_review_reasons.map((r, i) => (
                  <li key={i} className="text-xs text-amber-700">
                    • {r}
                  </li>
                ))}
              </ul>
            )}
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <ReviewPanel returnId={result.return_id} userRole={userRole} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── ResultPage ────────────────────────────────────────────────────────────────
interface ResultPageProps {
  result: DecisionOutput;
  userRole?: string;
  onBack?: () => void;
}

export default function ResultPage({
  result,
  userRole = 'viewer',
  onBack,
}: ResultPageProps) {
  return (
    <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
      <div className="flex items-center gap-3">
        {onBack && (
          <Button
            id="result-back"
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="h-7 rounded-full text-xs text-neutral-500 hover:text-black"
          >
            ← Back
          </Button>
        )}
        <h1 className="text-lg font-semibold text-neutral-950">
          Return Analysis Result
        </h1>
      </div>
      <DecisionCard result={result} userRole={userRole} />
    </div>
  );
}
