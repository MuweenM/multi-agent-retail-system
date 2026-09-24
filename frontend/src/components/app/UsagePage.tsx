import { useState, useEffect } from 'react';
import { UsageResponse } from '@/types/contracts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/spinner';
import { getUsage } from '@/lib/api';
import { BarChart2, Zap, TrendingUp, AlertCircle } from 'lucide-react';

export default function UsagePage() {
  const [data, setData] = useState<UsageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getUsage();
        setData(res);
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : 'Failed to load usage data.'
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="h-6 w-6 text-neutral-400" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertCircle className="h-4 w-4" />
          {error || 'No usage data available.'}
        </div>
      </div>
    );
  }

  const returnsUsed = data.usage.total_returns;
  const returnsLimit = data.plan_limits.included_returns;
  const returnsPercent =
    returnsLimit > 0
      ? Math.min(100, Math.round((returnsUsed / returnsLimit) * 100))
      : 0;

  const apiUsed = data.usage.api_call;
  const apiLimit = data.plan_limits.included_api_calls;
  const apiPercent =
    apiLimit > 0 ? Math.min(100, Math.round((apiUsed / apiLimit) * 100)) : 0;

  const getProgressColor = (pct: number) => {
    if (pct >= 90) return 'bg-rose-500';
    if (pct >= 70) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold tracking-tight text-neutral-950">
            Usage &amp; Plan
          </h1>
          <p className="text-sm text-neutral-500">
            {data.month} · Tenant{' '}
            <span className="font-mono text-neutral-700">{data.tenant_id}</span>
          </p>
        </div>
        <Badge
          variant="outline"
          className="rounded-full border-neutral-200 bg-neutral-100 px-3 py-1 font-mono text-xs text-neutral-700"
        >
          {data.tier} plan
        </Badge>
      </div>

      {/* Invoice Card */}
      <Card className="rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none">
        <CardContent className="flex items-center justify-between gap-6 p-6">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-neutral-400">
              Estimated Invoice
            </p>
            <p className="mt-1 font-mono text-3xl font-semibold tracking-tight text-white">
              LKR {data.estimated_invoice_lkr.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-neutral-400">
              Based on current month usage
            </p>
          </div>
          <TrendingUp className="h-10 w-10 text-neutral-600" />
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Returns */}
        <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                Returns Processed
              </CardTitle>
              <BarChart2 className="h-4 w-4 text-neutral-400" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3 p-5 pt-0">
            <div className="flex items-end justify-between">
              <span className="font-mono text-2xl font-semibold text-neutral-950">
                {returnsUsed.toLocaleString()}
              </span>
              <span className="font-mono text-xs text-neutral-400">
                / {returnsLimit > 0 ? returnsLimit.toLocaleString() : '∞'}
              </span>
            </div>
            {returnsLimit > 0 && (
              <>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-100">
                  <div
                    className={`h-full rounded-full transition-all ${getProgressColor(returnsPercent)}`}
                    style={{ width: `${returnsPercent}%` }}
                  />
                </div>
                <p className="text-[11px] text-neutral-400">
                  {returnsPercent}% of plan limit used
                  {returnsPercent >= 90 && (
                    <span className="ml-2 font-medium text-rose-600">
                      Approaching limit
                    </span>
                  )}
                </p>
              </>
            )}
            <div className="grid grid-cols-2 gap-2 text-[11px] text-neutral-500">
              <span>Single: {data.usage.return_processed}</span>
              <span>Bulk rows: {data.usage.bulk_row}</span>
            </div>
          </CardContent>
        </Card>

        {/* API Calls */}
        <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                API Calls
              </CardTitle>
              <Zap className="h-4 w-4 text-neutral-400" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3 p-5 pt-0">
            <div className="flex items-end justify-between">
              <span className="font-mono text-2xl font-semibold text-neutral-950">
                {apiUsed.toLocaleString()}
              </span>
              <span className="font-mono text-xs text-neutral-400">
                / {apiLimit > 0 ? apiLimit.toLocaleString() : '∞'}
              </span>
            </div>
            {apiLimit > 0 && (
              <>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-100">
                  <div
                    className={`h-full rounded-full transition-all ${getProgressColor(apiPercent)}`}
                    style={{ width: `${apiPercent}%` }}
                  />
                </div>
                <p className="text-[11px] text-neutral-400">
                  {apiPercent}% of plan limit used
                  {apiPercent >= 90 && (
                    <span className="ml-2 font-medium text-rose-600">
                      Approaching limit
                    </span>
                  )}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* LLM Tokens */}
      <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-neutral-500">
                LLM Tokens Used
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-neutral-950">
                {data.usage.llm_tokens.toLocaleString()}
              </p>
            </div>
            <Badge
              variant="outline"
              className="rounded-full border-neutral-200 bg-neutral-100 font-mono text-[10px] text-neutral-600"
            >
              Metered
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Notice */}
      {returnsPercent >= 80 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <p className="text-sm font-semibold text-amber-900">
            You are approaching your plan's return limit.
          </p>
          <p className="mt-1 text-xs text-amber-700">
            Upgrade to <strong>Business</strong> (LKR 22,500/month) to get 3,000
            included returns, bulk processing, and priority support. Contact
            your admin or visit{' '}
            <a href="#/billing" className="underline">
              Billing &amp; Plans
            </a>
            .
          </p>
        </div>
      )}
    </div>
  );
}
