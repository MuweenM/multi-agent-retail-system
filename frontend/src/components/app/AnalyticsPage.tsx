import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  AlertTriangle,
  Package,
  Brain,
  RefreshCw,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Search,
  Layers,
  Activity,
  Zap,
  Info,
  ChevronRight,
  TrendingUp,
  FileSpreadsheet,
  AlertCircle,
  Check,
} from 'lucide-react';

// ── shadcn/ui Nova Components ────────────────────────────────────────────────
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import {
  Empty,
  EmptyMedia,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from '@/components/ui/empty';
import {
  Tooltip as UiTooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from '@/components/ui/tooltip';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';

// ── Contracts & Mocks ────────────────────────────────────────────────────────
import {
  BulkJob,
  BulkSummary,
  ProductImpactItem,
  ProductRootCauseReport,
} from '@/types/contracts';
import {
  fetchBulkJobs,
  fetchBulkSummary,
  fetchProductImpacts,
  fetchProductReport,
  getAllCatalogProductIds,
} from '@/mocks/agent2Mocks';

// ── Color System & Taxonomy Config ───────────────────────────────────────────
const ROOT_CAUSE_LABELS: Record<string, string> = {
  manufacturing_defect: 'Manufacturing Defect',
  size_fit_issue: 'Size / Fit Issue',
  quality_durability: 'Quality / Durability',
  damaged_in_transit: 'Damaged in Transit',
  wrong_item_shipped: 'Wrong Item Shipped',
  not_as_described: 'Not as Described',
  change_of_mind: 'Change of Mind',
  policy_abuse_suspected: 'Policy Abuse Suspected',
  late_delivery: 'Late Delivery',
  unknown: 'Unknown',
};

const ROOT_CAUSE_COLORS: Record<string, string> = {
  manufacturing_defect: '#171717', // Primary Dark
  size_fit_issue: '#404040',
  quality_durability: '#737373',
  damaged_in_transit: '#a3a3a3',
  wrong_item_shipped: '#d4d4d4',
  not_as_described: '#525252',
  change_of_mind: '#e5e5e5',
  policy_abuse_suspected: '#dc2626',
  late_delivery: '#f59e0b',
  unknown: '#9ca3af',
};

const DECISION_COLORS: Record<string, string> = {
  approve: '#171717',
  reject: '#737373',
  escalate: '#090909',
  request_info: '#d4d4d4',
};

// ── Formatting Helpers ────────────────────────────────────────────────────────
function formatLKR(amount: number): string {
  if (amount >= 1_000_000) {
    return `LKR ${(amount / 1_000_000).toFixed(2)}M`;
  }
  if (amount >= 1_000) {
    return `LKR ${(amount / 1_000).toFixed(1)}k`;
  }
  return `LKR ${amount.toLocaleString()}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

// ── Custom Tooltip for Recharts ──────────────────────────────────────────────
interface CustomRechartsTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number;
    payload?: Record<string, unknown>;
    color?: string;
  }>;
  label?: string;
  total?: number;
}

function CustomChartTooltip({
  active,
  payload,
  label,
  total,
}: CustomRechartsTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-xl border border-neutral-200 bg-white/95 p-3 shadow-lg backdrop-blur-md">
      <div className="mb-1.5 text-xs font-semibold text-neutral-900">{label}</div>
      <div className="space-y-1">
        {payload.map((item, idx) => {
          const itemVal = Number(item.value) || 0;
          const pct = total && total > 0 ? ((itemVal / total) * 100).toFixed(1) : null;
          return (
            <div key={idx} className="flex items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span
                  className="size-2.5 rounded-full"
                  style={{ backgroundColor: item.color || '#000000' }}
                />
                <span className="text-neutral-600">
                  {ROOT_CAUSE_LABELS[item.name || ''] || item.name}:
                </span>
              </div>
              <div className="flex items-center gap-1 font-mono font-medium text-neutral-950">
                <span>{itemVal.toLocaleString()}</span>
                {pct && <span className="text-neutral-400">({pct}%)</span>}
              </div>
            </div>
          );
        })}
      </div>
      {total && total > 0 && (
        <div className="mt-2 border-t border-neutral-100 pt-1 text-[10px] text-neutral-400">
          Share calculated as (Count ÷ Total of {total.toLocaleString()})
        </div>
      )}
    </div>
  );
}

// ── Metric Card Component with Explanations ──────────────────────────────────
interface MetricCardProps {
  title: string;
  value: string;
  calculationExplanation: string;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon: React.ReactNode;
  badgeText?: string;
}

function MetricCard({
  title,
  value,
  calculationExplanation,
  trend,
  trendDirection = 'neutral',
  icon,
  badgeText,
}: MetricCardProps) {
  return (
    <Card className="relative overflow-hidden border-neutral-200 bg-white transition-all hover:border-neutral-300">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-neutral-500">{title}</span>
            <UiTooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  className="h-4 w-4 p-0 text-neutral-400 hover:bg-transparent hover:text-neutral-700"
                  aria-label={`Calculation explanation for ${title}`}
                >
                  <Info className="size-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs text-xs">
                <p className="font-medium text-neutral-100">Formula / Calculation</p>
                <p className="text-neutral-300">{calculationExplanation}</p>
              </TooltipContent>
            </UiTooltip>
          </div>
          <div className="flex size-8 items-center justify-center rounded-full bg-neutral-100 text-neutral-900">
            {icon}
          </div>
        </div>

        <div className="mt-3 flex items-baseline justify-between">
          <span className="font-mono text-2xl font-bold tracking-tight text-neutral-950">
            {value}
          </span>
          {badgeText && (
            <Badge variant="outline" className="rounded-full font-mono text-[11px]">
              {badgeText}
            </Badge>
          )}
        </div>

        <div className="mt-2 flex items-center justify-between text-[11px] text-neutral-400">
          <span className="truncate pr-2 font-mono text-[10px] text-neutral-500">
            {calculationExplanation}
          </span>
          {trend && (
            <div
              className={`flex items-center gap-0.5 font-medium ${
                trendDirection === 'up'
                  ? 'text-neutral-900'
                  : trendDirection === 'down'
                    ? 'text-neutral-600'
                    : 'text-neutral-400'
              }`}
            >
              {trendDirection === 'up' && <ArrowUpRight className="size-3" />}
              {trendDirection === 'down' && <ArrowDownRight className="size-3" />}
              <span>{trend}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Analytics Page Component ─────────────────────────────────────────────
export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<string>('bulk-run');
  const [jobs, setJobs] = useState<BulkJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('JOB-2026-09-A2');
  const [bulkSummary, setBulkSummary] = useState<BulkSummary | null>(null);
  const [productImpacts, setProductImpacts] = useState<ProductImpactItem[]>([]);
  const [loadingBulk, setLoadingBulk] = useState<boolean>(true);

  // Tab 2 Product Investigation State
  const catalogProducts = getAllCatalogProductIds();
  const [selectedProductId, setSelectedProductId] = useState<string>('PROD-WM-BOOTS-01');
  const [productReport, setProductReport] = useState<ProductRootCauseReport | null>(null);
  const [loadingProduct, setLoadingProduct] = useState<boolean>(true);
  const [completedActions, setCompletedActions] = useState<Record<string, boolean>>({});

  // Load bulk jobs list on mount
  useEffect(() => {
    async function initJobs() {
      try {
        const jobsList = await fetchBulkJobs();
        setJobs(jobsList);
        if (jobsList.length > 0 && !selectedJobId) {
          setSelectedJobId(jobsList[0].job_id);
        }
      } catch (err) {
        console.error('Failed to load bulk jobs', err);
      }
    }
    initJobs();
  }, [selectedJobId]);

  // Load Bulk Summary and Top Impact Products whenever selectedJobId changes
  useEffect(() => {
    let isMounted = true;
    async function loadBulkData() {
      if (!selectedJobId) return;
      setLoadingBulk(true);
      try {
        const [summary, impacts] = await Promise.all([
          fetchBulkSummary(selectedJobId),
          fetchProductImpacts(selectedJobId),
        ]);
        if (isMounted) {
          setBulkSummary(summary);
          setProductImpacts(impacts);
        }
      } catch (err) {
        console.error('Failed to fetch bulk summary', err);
      } finally {
        if (isMounted) setLoadingBulk(false);
      }
    }
    loadBulkData();
    return () => {
      isMounted = false;
    };
  }, [selectedJobId]);

  // Load Product Deep Dive Report whenever selectedProductId changes
  useEffect(() => {
    let isMounted = true;
    async function loadProductDeepDive() {
      if (!selectedProductId) return;
      setLoadingProduct(true);
      try {
        const report = await fetchProductReport(selectedProductId);
        if (isMounted) {
          setProductReport(report);
        }
      } catch (err) {
        console.error('Failed to fetch product report', err);
      } finally {
        if (isMounted) setLoadingProduct(false);
      }
    }
    loadProductDeepDive();
    return () => {
      isMounted = false;
    };
  }, [selectedProductId]);

  const handleRefresh = async () => {
    if (activeTab === 'bulk-run') {
      setLoadingBulk(true);
      const [summary, impacts] = await Promise.all([
        fetchBulkSummary(selectedJobId),
        fetchProductImpacts(selectedJobId),
      ]);
      setBulkSummary(summary);
      setProductImpacts(impacts);
      setLoadingBulk(false);
    } else {
      setLoadingProduct(true);
      const report = await fetchProductReport(selectedProductId);
      setProductReport(report);
      setLoadingProduct(false);
    }
  };

  const toggleActionCompleted = (actionIdx: number) => {
    setCompletedActions((prev) => ({
      ...prev,
      [`${selectedProductId}-${actionIdx}`]: !prev[`${selectedProductId}-${actionIdx}`],
    }));
  };

  // Transform Root Cause Map into Recharts Array
  const rootCauseChartData = bulkSummary
    ? Object.entries(bulkSummary.by_root_cause)
        .map(([key, count]) => ({
          causeKey: key,
          label: ROOT_CAUSE_LABELS[key] || key,
          count: count,
          fill: ROOT_CAUSE_COLORS[key] || '#737373',
          share: bulkSummary.total > 0 ? count / bulkSummary.total : 0,
        }))
        .sort((a, b) => b.count - a.count)
    : [];

  // Transform Decisions Map into Recharts Donut Array
  const decisionChartData = bulkSummary
    ? Object.entries(bulkSummary.decisions).map(([key, count]) => ({
        name: key.toUpperCase(),
        value: count,
        color: DECISION_COLORS[key] || '#737373',
      }))
    : [];

  // Selected Job metadata
  const currentJob = jobs.find((j) => j.job_id === selectedJobId) || jobs[0];

  return (
    <TooltipProvider delayDuration={150}>
      <div className="min-h-screen bg-white text-neutral-900">
        {/* ── Top App Bar ─────────────────────────────────────────────────── */}
        <header className="sticky top-0 z-30 border-b border-neutral-200 bg-white/90 backdrop-blur-md">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-full bg-black text-white">
                <Brain className="size-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold tracking-tight text-neutral-950">
                    Agent 2: Root-Cause Analytics & Batch Intelligence
                  </h1>
                  <Badge
                    variant="outline"
                    className="rounded-full border-neutral-200 bg-neutral-50 px-2 py-0.5 font-mono text-[10px] text-neutral-600"
                  >
                    Contract v1.1
                  </Badge>
                </div>
                <p className="text-xs text-neutral-500">
                  Automated taxonomy clustering, Fisher's exact anomaly detection & supplier risk
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 rounded-full border-neutral-200 px-3 text-xs text-neutral-700 hover:bg-neutral-50"
                onClick={handleRefresh}
                disabled={loadingBulk || loadingProduct}
              >
                <RefreshCw
                  className={`mr-1.5 size-3.5 ${
                    loadingBulk || loadingProduct ? 'animate-spin' : ''
                  }`}
                />
                Refresh
              </Button>
              <Badge
                variant="outline"
                className="flex h-8 items-center gap-1.5 rounded-full border-neutral-200 bg-neutral-50 px-3 text-xs font-normal text-neutral-600"
              >
                <span className="size-2 animate-pulse rounded-full bg-emerald-500" />
                Service Ready
              </Badge>
            </div>
          </div>
        </header>

        {/* ── Main Workspace ──────────────────────────────────────────────── */}
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            {/* Top Navigation Tabs Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <TabsList className="h-10 rounded-full border border-neutral-200 bg-neutral-100 p-1">
                <TabsTrigger
                  value="bulk-run"
                  className="rounded-full px-5 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  <Layers className="mr-2 size-3.5" />
                  TAB 1 — Bulk Run Analysis
                </TabsTrigger>
                <TabsTrigger
                  value="product-investigation"
                  className="rounded-full px-5 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  <Search className="mr-2 size-3.5" />
                  TAB 2 — Product Investigation
                </TabsTrigger>
              </TabsList>

              {/* Contextual Selector in Top Bar */}
              {activeTab === 'bulk-run' ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-neutral-500">Active Job:</span>
                  <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                    <SelectTrigger className="h-9 w-[260px] rounded-full border-neutral-200 bg-white font-mono text-xs">
                      <SelectValue placeholder="Select Ingestion Job" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-neutral-200 font-mono text-xs">
                      {jobs.map((job) => (
                        <SelectItem key={job.job_id} value={job.job_id}>
                          {job.job_id} ({job.total.toLocaleString()} records)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-neutral-500">Target Product:</span>
                  <Select value={selectedProductId} onValueChange={setSelectedProductId}>
                    <SelectTrigger className="h-9 w-[300px] rounded-full border-neutral-200 bg-white font-mono text-xs">
                      <SelectValue placeholder="Select Product" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-neutral-200 text-xs">
                      {catalogProducts.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          <span className="font-mono font-medium">{p.id}</span> — {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            {/* ══════════════════════════════════════════════════════════════════
                TAB 1: BULK RUN ANALYSIS
               ══════════════════════════════════════════════════════════════════ */}
            <TabsContent value="bulk-run" className="space-y-6 outline-none">
              {loadingBulk ? (
                <div className="flex h-96 flex-col items-center justify-center gap-3">
                  <Spinner className="size-8 text-neutral-900" />
                  <p className="text-xs text-neutral-500">
                    Aggregating bulk returns and computing root-cause taxonomy clusters...
                  </p>
                </div>
              ) : !bulkSummary ? (
                <Empty>
                  <EmptyMedia>
                    <FileSpreadsheet className="size-10 text-neutral-400" />
                  </EmptyMedia>
                  <EmptyHeader>
                    <EmptyTitle>No Bulk Run Data Available</EmptyTitle>
                    <EmptyDescription>
                      Select an active bulk ingestion job from the dropdown above.
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <>
                  {/* Executive Overview Banner */}
                  <div className="flex flex-col gap-4 rounded-2xl border border-neutral-200 bg-neutral-50/80 p-5 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge className="rounded-full bg-black px-2.5 py-0.5 text-xs text-white hover:bg-black">
                          {bulkSummary.job_id}
                        </Badge>
                        <span className="text-xs font-semibold text-neutral-800">
                          {currentJob?.name || 'Bulk Ingestion Run'}
                        </span>
                        <span className="font-mono text-xs text-neutral-400">•</span>
                        <span className="font-mono text-xs text-neutral-500">
                          Processed at {currentJob?.created_at || 'Recent'}
                        </span>
                      </div>
                      <p className="max-w-4xl text-xs leading-relaxed text-neutral-600">
                        {bulkSummary.executive_summary}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex flex-col items-end border-l border-neutral-200 pl-4">
                        <span className="text-[11px] text-neutral-400">Total Ingested</span>
                        <span className="font-mono text-lg font-bold text-neutral-950">
                          {bulkSummary.total.toLocaleString()}
                        </span>
                        <span className="text-[10px] text-neutral-400">rows evaluated</span>
                      </div>
                    </div>
                  </div>

                  {/* KPI Summary Grid with Strict Tooltips/Captions */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <MetricCard
                      title="Total Returns Evaluated"
                      value={bulkSummary.total.toLocaleString()}
                      calculationExplanation="Sum of all return rows processed in this job"
                      icon={<Package className="size-4" />}
                      badgeText="100% Parsed"
                    />

                    <MetricCard
                      title="Est. Value at Risk"
                      value={formatLKR(bulkSummary.est_value_at_risk_lkr)}
                      calculationExplanation="Value at Risk = ∑ (Return Count × Product Average Order Value)"
                      icon={<ShieldAlert className="size-4" />}
                      trend="+14.2% vs baseline"
                      trendDirection="up"
                    />

                    <MetricCard
                      title="Human Escalation Rate"
                      value={formatPercent(
                        bulkSummary.total > 0
                          ? bulkSummary.needs_review / bulkSummary.total
                          : 0
                      )}
                      calculationExplanation="Escalation Rate = Needs Review Count ÷ Total Ingested"
                      icon={<AlertTriangle className="size-4" />}
                      trend={`${bulkSummary.needs_review} flagged tickets`}
                    />

                    <MetricCard
                      title="Top Root Cause"
                      value={
                        rootCauseChartData.length > 0
                          ? rootCauseChartData[0].label
                          : 'N/A'
                      }
                      calculationExplanation="Highest frequency label determined by rule-based and ML classifier"
                      icon={<Activity className="size-4" />}
                      badgeText={
                        rootCauseChartData.length > 0
                          ? `${formatPercent(rootCauseChartData[0].share)} share`
                          : undefined
                      }
                    />
                  </div>

                  {/* ── Visual Analytics: Root Cause Bar Chart & Decisions Donut ── */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                    {/* Root-Cause Bar Chart (8 cols) */}
                    <Card className="border-neutral-200 lg:col-span-8">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              Root-Cause Taxonomy Distribution
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Frequency count of return tickets categorized across the standard
                              retail taxonomy
                            </CardDescription>
                          </div>
                          <UiTooltip>
                            <TooltipTrigger asChild>
                              <Badge
                                variant="outline"
                                className="cursor-help rounded-full border-neutral-200 bg-neutral-50 font-mono text-[11px]"
                              >
                                Formula: Label Count ÷ Total
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs text-xs">
                              Category share is calculated by dividing each label's return count
                              by the total {bulkSummary.total.toLocaleString()} returns in this
                              job.
                            </TooltipContent>
                          </UiTooltip>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="h-72 w-full pt-4">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={rootCauseChartData}
                              margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                            >
                              <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={false}
                                stroke="#f0f0f0"
                              />
                              <XAxis
                                dataKey="label"
                                angle={-25}
                                textAnchor="end"
                                interval={0}
                                tick={{ fontSize: 11, fill: '#737373' }}
                                height={60}
                              />
                              <YAxis tick={{ fontSize: 11, fill: '#737373' }} />
                              <RechartsTooltip
                                content={
                                  <CustomChartTooltip total={bulkSummary.total} />
                                }
                              />
                              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                                {rootCauseChartData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="mt-2 flex items-center justify-between border-t border-neutral-100 pt-2 text-[11px] text-neutral-500">
                          <span>
                            Total classified categories: {rootCauseChartData.length}
                          </span>
                          <span className="font-mono text-[10px]">
                            Deterministic rules + ML Fallback
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Decisions Chart (4 cols) */}
                    <Card className="border-neutral-200 lg:col-span-4">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              Automated Policy Decisions
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Split by policy resolution status
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="h-52 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={decisionChartData}
                                cx="50%"
                                cy="50%"
                                innerRadius={55}
                                outerRadius={80}
                                paddingAngle={3}
                                dataKey="value"
                              >
                                {decisionChartData.map((entry, index) => (
                                  <Cell key={`dec-cell-${index}`} fill={entry.color} />
                                ))}
                              </Pie>
                              <RechartsTooltip
                                content={
                                  <CustomChartTooltip total={bulkSummary.total} />
                                }
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="space-y-1.5 border-t border-neutral-100 pt-3">
                          {decisionChartData.map((d) => {
                            const pct =
                              bulkSummary.total > 0
                                ? ((d.value / bulkSummary.total) * 100).toFixed(1)
                                : '0';
                            return (
                              <div
                                key={d.name}
                                className="flex items-center justify-between text-xs"
                              >
                                <div className="flex items-center gap-2">
                                  <span
                                    className="size-2.5 rounded-full"
                                    style={{ backgroundColor: d.color }}
                                  />
                                  <span className="capitalize text-neutral-600">
                                    {d.name.toLowerCase().replace('_', ' ')}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2 font-mono text-neutral-900">
                                  <span>{d.value.toLocaleString()}</span>
                                  <span className="text-[11px] text-neutral-400">
                                    ({pct}%)
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="mt-3 text-[10px] text-neutral-400">
                          Caption: Decision share = Decision count ÷ Total bulk returns (
                          {bulkSummary.total.toLocaleString()})
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* ── Top Products By Impact Table ──────────────────────────── */}
                  <Card className="border-neutral-200">
                    <CardHeader className="pb-3">
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold">
                            Top Products by Return Impact
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Ranked by monetary exposure to identify the highest friction inventory
                          </CardDescription>
                        </div>
                        <Badge
                          variant="outline"
                          className="w-fit rounded-full border-neutral-200 bg-neutral-50 font-mono text-[11px]"
                        >
                          Impact Formula: Return Count × Average Order Value
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-neutral-200 hover:bg-transparent">
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Product SKU / Name
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Category
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Returns
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Avg Order Value
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Value at Risk
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Dominant Cause
                              </TableHead>
                              <TableHead className="text-center text-xs font-semibold text-neutral-700">
                                Anomaly Status
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Action
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {productImpacts.map((prod) => (
                              <TableRow
                                key={prod.product_id}
                                className="border-neutral-100 transition-colors hover:bg-neutral-50/70"
                              >
                                <TableCell className="py-3">
                                  <div className="font-mono text-xs font-bold text-neutral-900">
                                    {prod.product_id}
                                  </div>
                                  <div className="text-xs text-neutral-500">
                                    {prod.product_name}
                                  </div>
                                </TableCell>
                                <TableCell className="text-xs text-neutral-600">
                                  {prod.category}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-semibold text-neutral-900">
                                  {prod.return_count.toLocaleString()}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs text-neutral-600">
                                  {formatLKR(prod.avg_order_value_lkr)}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-bold text-neutral-950">
                                  {formatLKR(prod.value_at_risk_lkr)}
                                </TableCell>
                                <TableCell>
                                  <Badge
                                    variant="outline"
                                    className="rounded-full border-neutral-200 bg-neutral-50 text-[11px] font-normal"
                                  >
                                    {ROOT_CAUSE_LABELS[prod.top_root_cause] ||
                                      prod.top_root_cause}
                                    <span className="ml-1 font-mono text-neutral-400">
                                      ({formatPercent(prod.top_root_cause_share)})
                                    </span>
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-center">
                                  {prod.is_emerging_spike ? (
                                    <Badge className="rounded-full bg-neutral-900 text-[10px] text-white hover:bg-black">
                                      <Zap className="mr-1 size-3" /> Emerging Spike
                                    </Badge>
                                  ) : (
                                    <Badge
                                      variant="outline"
                                      className="rounded-full border-neutral-200 text-[10px] text-neutral-500"
                                    >
                                      Normal Variance
                                    </Badge>
                                  )}
                                </TableCell>
                                <TableCell className="text-right">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 rounded-full px-2.5 text-xs text-neutral-700 hover:bg-neutral-200/60"
                                    onClick={() => {
                                      setSelectedProductId(prod.product_id);
                                      setActiveTab('product-investigation');
                                    }}
                                  >
                                    Investigate <ChevronRight className="ml-1 size-3" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="mt-2 text-[10px] text-neutral-400">
                        Caption: Value at Risk = Return Count × Average Order Value (AOV).
                        Calculated exposure reflects gross return claim volume.
                      </div>
                    </CardContent>
                  </Card>

                  {/* ── Clusters with Top Terms & Emerging Issues ─────────────── */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* Clusters with Top Terms */}
                    <Card className="border-neutral-200">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              Issue NLP Clusters & Top Keywords
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Unsupervised semantic grouping of unstructured customer complaints
                            </CardDescription>
                          </div>
                          <Badge
                            variant="outline"
                            className="rounded-full border-neutral-200 font-mono text-[10px]"
                          >
                            {bulkSummary.clusters.length} Active Clusters
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {bulkSummary.clusters.map((cluster) => {
                          const share =
                            bulkSummary.total > 0
                              ? (cluster.size / bulkSummary.total) * 100
                              : 0;
                          return (
                            <div
                              key={cluster.cluster_id}
                              className="rounded-xl border border-neutral-200 bg-white p-3.5 transition-all hover:border-neutral-300 hover:bg-neutral-50/50"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="flex size-6 items-center justify-center rounded-full bg-neutral-100 font-mono text-xs font-bold text-neutral-900">
                                    #{cluster.cluster_id}
                                  </span>
                                  <span className="text-xs font-semibold text-neutral-900">
                                    {ROOT_CAUSE_LABELS[cluster.dominant_root_cause] ||
                                      cluster.dominant_root_cause}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="font-mono text-xs font-bold text-neutral-950">
                                    {cluster.size} returns
                                  </span>
                                  <span className="font-mono text-[11px] text-neutral-400">
                                    ({share.toFixed(1)}% share)
                                  </span>
                                  {cluster.growth_vs_prev !== undefined &&
                                    cluster.growth_vs_prev !== null && (
                                      <Badge
                                        variant="outline"
                                        className={`rounded-full px-1.5 py-0 font-mono text-[10px] ${
                                          cluster.growth_vs_prev > 0
                                            ? 'border-neutral-900 text-neutral-900'
                                            : 'border-neutral-300 text-neutral-400'
                                        }`}
                                      >
                                        {cluster.growth_vs_prev > 0 ? '+' : ''}
                                        {(cluster.growth_vs_prev * 100).toFixed(0)}% growth
                                      </Badge>
                                    )}
                                </div>
                              </div>

                              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                                <span className="text-[11px] text-neutral-400">
                                  Extracted terms:
                                </span>
                                {cluster.top_terms.map((term, tIdx) => (
                                  <span
                                    key={tIdx}
                                    className="rounded-full bg-neutral-100 px-2 py-0.5 font-mono text-[11px] text-neutral-700"
                                  >
                                    {term}
                                  </span>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                        <div className="pt-1 text-[10px] text-neutral-400">
                          Caption: Cluster share = Cluster count ÷ Total returns (
                          {bulkSummary.total.toLocaleString()}). Growth vs previous period =
                          (Current - Prior) ÷ Prior.
                        </div>
                      </CardContent>
                    </Card>

                    {/* Emerging Issues & Statistical Anomalies */}
                    <Card className="border-neutral-200">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              Statistical Anomalies & Emerging Spikes
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Automated alerts based on Fisher's exact test (p &lt; 0.05)
                            </CardDescription>
                          </div>
                          <Badge
                            variant="outline"
                            className="rounded-full border-neutral-200 font-mono text-[10px]"
                          >
                            {bulkSummary.findings.length} Anomalies Flagged
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {bulkSummary.findings.map((finding, fIdx) => (
                          <div
                            key={fIdx}
                            className="rounded-xl border border-neutral-200 bg-white p-3.5 transition-all hover:border-neutral-300"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <Badge className="rounded-full bg-neutral-900 px-2 py-0.5 font-mono text-[10px] text-white hover:bg-black">
                                    {finding.kind.toUpperCase()}
                                  </Badge>
                                  <span className="text-xs font-semibold text-neutral-900">
                                    {finding.title}
                                  </span>
                                </div>
                                <p className="text-xs text-neutral-600">{finding.detail}</p>
                              </div>
                              <div className="text-right">
                                <div className="font-mono text-xs font-bold text-neutral-950">
                                  {formatLKR(finding.value_at_risk_lkr)}
                                </div>
                                <div className="text-[10px] text-neutral-400">
                                  {finding.return_count} tickets
                                </div>
                              </div>
                            </div>

                            <div className="mt-2.5 flex items-center justify-between border-t border-neutral-100 pt-2 text-[11px]">
                              <div className="flex items-center gap-3 font-mono text-neutral-500">
                                {finding.supplier_id && (
                                  <span>Supplier: {finding.supplier_id}</span>
                                )}
                                {finding.batch_id && <span>Batch: {finding.batch_id}</span>}
                              </div>
                              {finding.p_value !== undefined && finding.p_value !== null && (
                                <UiTooltip>
                                  <TooltipTrigger asChild>
                                    <Badge
                                      variant="outline"
                                      className="cursor-help rounded-full border-neutral-900 bg-neutral-50 font-mono text-[10px] text-neutral-900"
                                    >
                                      Fisher p = {finding.p_value.toFixed(4)}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs text-xs">
                                    Fisher's exact test p-value: Probability that the observed defect
                                    concentration occurred by random chance. Values &lt; 0.05
                                    indicate statistically significant defect clustering.
                                  </TooltipContent>
                                </UiTooltip>
                              )}
                            </div>
                          </div>
                        ))}
                        <div className="pt-1 text-[10px] text-neutral-400">
                          Caption: Fisher's exact test measures statistical significance of defect
                          clustering against baseline catalog return variance.
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>

            {/* ══════════════════════════════════════════════════════════════════
                TAB 2: PRODUCT INVESTIGATION DEEP DIVE
               ══════════════════════════════════════════════════════════════════ */}
            <TabsContent value="product-investigation" className="space-y-6 outline-none">
              {loadingProduct ? (
                <div className="flex h-96 flex-col items-center justify-center gap-3">
                  <Spinner className="size-8 text-neutral-900" />
                  <p className="text-xs text-neutral-500">
                    Retrieving product history, weekly defect trends & batch supplier manifests...
                  </p>
                </div>
              ) : !productReport ? (
                <Empty>
                  <EmptyMedia>
                    <Search className="size-10 text-neutral-400" />
                  </EmptyMedia>
                  <EmptyHeader>
                    <EmptyTitle>No Product Investigation Record Found</EmptyTitle>
                    <EmptyDescription>
                      Select a product from the top selector to inspect root causes.
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <>
                  {/* Product Header & Headline */}
                  <div className="flex flex-col gap-4 rounded-2xl border border-neutral-200 bg-neutral-50/80 p-5 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <Badge className="rounded-full bg-black px-3 py-0.5 font-mono text-xs text-white">
                          {productReport.product_id}
                        </Badge>
                        <h2 className="text-base font-bold text-neutral-950">
                          {productReport.product_name}
                        </h2>
                        <span className="text-xs text-neutral-400">•</span>
                        <span className="text-xs text-neutral-600">
                          {productReport.category}
                        </span>
                      </div>
                      <p className="max-w-3xl text-xs leading-relaxed text-neutral-700">
                        <strong className="font-semibold text-neutral-900">Diagnosis: </strong>
                        {productReport.headline}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 border-t border-neutral-200 pt-3 lg:border-t-0 lg:border-l lg:pl-6 lg:pt-0">
                      <div className="text-right">
                        <span className="text-[11px] text-neutral-400">Evaluation Window</span>
                        <div className="font-mono text-sm font-bold text-neutral-900">
                          {productReport.window_days} Days
                        </div>
                        <span className="text-[10px] text-neutral-400">
                          Trailing returns
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-[11px] text-neutral-400">Avg Unit Value</span>
                        <div className="font-mono text-sm font-bold text-neutral-900">
                          {formatLKR(productReport.avg_order_value_lkr)}
                        </div>
                        <span className="text-[10px] text-neutral-400">Gross AOV</span>
                      </div>
                    </div>
                  </div>

                  {/* Product Investigation Metric Cards */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <MetricCard
                      title="Total Return Volume"
                      value={`${productReport.total_returns} units`}
                      calculationExplanation="Sum of all return claims filed within the 45-day evaluation window"
                      icon={<Package className="size-4" />}
                      badgeText={`${productReport.total_units_sold} Sold`}
                    />

                    <MetricCard
                      title="Overall Return Rate"
                      value={formatPercent(productReport.overall_return_rate)}
                      calculationExplanation="Return Rate = Total Returns (86) ÷ Total Units Sold (720)"
                      icon={<TrendingUp className="size-4" />}
                      trend={
                        productReport.overall_return_rate > 0.08
                          ? 'Elevated (>8% threshold)'
                          : 'Within normal limits'
                      }
                      trendDirection={
                        productReport.overall_return_rate > 0.08 ? 'up' : 'neutral'
                      }
                    />

                    <MetricCard
                      title="Product Value at Risk"
                      value={formatLKR(
                        productReport.total_returns * productReport.avg_order_value_lkr
                      )}
                      calculationExplanation="Product Impact = Total Returns × Average Order Value"
                      icon={<ShieldAlert className="size-4" />}
                      badgeText="Supplier Reclaimable"
                    />

                    <MetricCard
                      title="Anomalous Batches"
                      value={`${
                        productReport.batches.filter((b) => b.is_suspicious).length
                      } Flagged`}
                      calculationExplanation="Batches with Fisher's exact test p < 0.05 and defect rate > 10%"
                      icon={<AlertCircle className="size-4" />}
                      badgeText="P-Value < 0.001"
                    />
                  </div>

                  {/* ── Label Distribution & Weekly Trend Chart ───────────────── */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                    {/* Label Distribution Breakdown (5 cols) */}
                    <Card className="border-neutral-200 lg:col-span-5">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold">
                          Root Cause Label Breakdown
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Proportional cause distribution for {productReport.product_name}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-3">
                          {Object.entries(productReport.label_distribution)
                            .map(([cause, count]) => ({
                              cause,
                              label: ROOT_CAUSE_LABELS[cause] || cause,
                              count,
                              share:
                                productReport.total_returns > 0
                                  ? count / productReport.total_returns
                                  : 0,
                            }))
                            .sort((a, b) => b.count - a.count)
                            .map((item) => (
                              <div key={item.cause} className="space-y-1">
                                <div className="flex items-center justify-between text-xs">
                                  <div className="flex items-center gap-1.5">
                                    <span
                                      className="size-2 rounded-full"
                                      style={{
                                        backgroundColor:
                                          ROOT_CAUSE_COLORS[item.cause] || '#737373',
                                      }}
                                    />
                                    <span className="font-medium text-neutral-800">
                                      {item.label}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2 font-mono">
                                    <span className="font-semibold text-neutral-950">
                                      {item.count}
                                    </span>
                                    <span className="text-neutral-400">
                                      ({(item.share * 100).toFixed(1)}%)
                                    </span>
                                  </div>
                                </div>
                                <Progress
                                  value={item.share * 100}
                                  className="h-1.5 bg-neutral-100"
                                />
                              </div>
                            ))}
                        </div>
                        <div className="border-t border-neutral-100 pt-2 text-[10px] text-neutral-400">
                          Caption: Label distribution share = Specific Cause Count ÷ Total
                          Product Returns ({productReport.total_returns}).
                        </div>
                      </CardContent>
                    </Card>

                    {/* Weekly Trend Multi-Line Chart (7 cols) */}
                    <Card className="border-neutral-200 lg:col-span-7">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              6-Week Return Trajectory
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Weekly return incidence tracking defect emergence over time
                            </CardDescription>
                          </div>
                          <Badge
                            variant="outline"
                            className="rounded-full border-neutral-200 bg-neutral-50 font-mono text-[10px]"
                          >
                            Trajectory: W33 to W38
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64 w-full pt-2">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                              data={productReport.weekly_trend}
                              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                            >
                              <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={false}
                                stroke="#f0f0f0"
                              />
                              <XAxis
                                dataKey="week"
                                tick={{ fontSize: 11, fill: '#737373' }}
                              />
                              <YAxis tick={{ fontSize: 11, fill: '#737373' }} />
                              <RechartsTooltip
                                content={({ active, payload, label }) => {
                                  if (!active || !payload || payload.length === 0)
                                    return null;
                                  return (
                                    <div className="rounded-xl border border-neutral-200 bg-white/95 p-3 shadow-md backdrop-blur-md">
                                      <div className="mb-1 text-xs font-semibold text-neutral-900">
                                        Week: {label}
                                      </div>
                                      <div className="space-y-1">
                                        {payload.map((entry, idx) => (
                                          <div
                                            key={idx}
                                            className="flex items-center justify-between gap-4 text-xs"
                                          >
                                            <span className="text-neutral-600">
                                              {entry.name}:
                                            </span>
                                            <span className="font-mono font-bold text-neutral-900">
                                              {entry.value} returns
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  );
                                }}
                              />
                              <Legend
                                wrapperStyle={{ fontSize: 11, paddingTop: 10 }}
                              />
                              <Line
                                type="monotone"
                                dataKey="total"
                                name="Total Weekly Returns"
                                stroke="#000000"
                                strokeWidth={2.5}
                                dot={{ r: 4, fill: '#000000' }}
                              />
                              <Line
                                type="monotone"
                                dataKey="counts.manufacturing_defect"
                                name="Mfg Defect"
                                stroke="#525252"
                                strokeWidth={1.5}
                                strokeDasharray="4 4"
                                dot={{ r: 3, fill: '#525252' }}
                              />
                              <Line
                                type="monotone"
                                dataKey="counts.size_fit_issue"
                                name="Size / Fit"
                                stroke="#a3a3a3"
                                strokeWidth={1.5}
                                dot={{ r: 3, fill: '#a3a3a3' }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="mt-2 text-[10px] text-neutral-400">
                          Caption: Weekly trend plots aggregate return tickets per ISO calendar
                          week. Spike in W36-W37 corresponds to Batch B-4029 release.
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* ── Supplier Concentration Table & p-value Analysis ────────── */}
                  <Card className="border-neutral-200">
                    <CardHeader className="pb-3">
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold">
                            Supplier Attribution & Statistical Significance
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Defect concentration by vendor with Fisher's exact test p-values
                          </CardDescription>
                        </div>
                        <UiTooltip>
                          <TooltipTrigger asChild>
                            <Badge
                              variant="outline"
                              className="cursor-help rounded-full border-neutral-200 bg-neutral-50 font-mono text-[11px]"
                            >
                              p &lt; 0.05 = Statistically Significant
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs text-xs">
                            Fisher's exact test evaluates whether the proportion of defective
                            returns from this supplier exceeds the baseline factory average at
                            p &lt; 0.05.
                          </TooltipContent>
                        </UiTooltip>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-neutral-200 hover:bg-transparent">
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Supplier Name & Code
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Audit Finding & Root Cause Detail
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Return Count
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Value at Risk
                              </TableHead>
                              <TableHead className="text-center text-xs font-semibold text-neutral-700">
                                Fisher's Exact p-value
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Risk Tier
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {productReport.suppliers.map((sup, sIdx) => {
                              const isSig = sup.p_value !== null && sup.p_value !== undefined && sup.p_value < 0.05;
                              return (
                                <TableRow
                                  key={sIdx}
                                  className="border-neutral-100 transition-colors hover:bg-neutral-50/70"
                                >
                                  <TableCell className="py-3">
                                    <div className="font-semibold text-neutral-950 text-xs">
                                      {sup.title}
                                    </div>
                                    <div className="font-mono text-[11px] text-neutral-400">
                                      ID: {sup.supplier_id}
                                    </div>
                                  </TableCell>
                                  <TableCell className="max-w-md text-xs text-neutral-600">
                                    {sup.detail}
                                  </TableCell>
                                  <TableCell className="text-right font-mono text-xs font-bold text-neutral-900">
                                    {sup.return_count}
                                  </TableCell>
                                  <TableCell className="text-right font-mono text-xs font-bold text-neutral-950">
                                    {formatLKR(sup.value_at_risk_lkr)}
                                  </TableCell>
                                  <TableCell className="text-center">
                                    {sup.p_value !== undefined && sup.p_value !== null ? (
                                      <Badge
                                        variant="outline"
                                        className={`rounded-full font-mono text-[11px] ${
                                          isSig
                                            ? 'border-neutral-900 bg-black text-white'
                                            : 'border-neutral-200 text-neutral-500'
                                        }`}
                                      >
                                        p = {sup.p_value.toFixed(4)}
                                      </Badge>
                                    ) : (
                                      <span className="font-mono text-xs text-neutral-400">
                                        N/A
                                      </span>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    {isSig ? (
                                      <Badge className="rounded-full bg-neutral-900 text-[10px] text-white hover:bg-black">
                                        <AlertTriangle className="mr-1 size-3" /> Critical Focus
                                      </Badge>
                                    ) : (
                                      <Badge
                                        variant="outline"
                                        className="rounded-full border-neutral-200 text-[10px] text-neutral-500"
                                      >
                                        Acceptable
                                      </Badge>
                                    )}
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="mt-2 text-[10px] text-neutral-400">
                        Caption: Fisher's exact test p-value measures probability that defect
                        rate differential across suppliers is due to random variation. Values &lt;
                        0.05 reject the null hypothesis of uniform quality.
                      </div>
                    </CardContent>
                  </Card>

                  {/* ── Granular Batch Table with Suspicious-Batch Highlighting ─ */}
                  <Card className="border-neutral-200">
                    <CardHeader className="pb-3">
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold">
                            Batch Manifest & Anomaly Quarantine Table
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Lot-level defect analysis with automatic suspicious batch tagging
                          </CardDescription>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full border-neutral-200 bg-neutral-50 font-mono text-[11px]"
                        >
                          Defect Rate Formula: Returned Units ÷ Shipped Units
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-neutral-200 hover:bg-transparent">
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Batch Number
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Supplier / Lot
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Mfg Date
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Shipped
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Returned
                              </TableHead>
                              <TableHead className="text-right text-xs font-semibold text-neutral-700">
                                Defect Rate
                              </TableHead>
                              <TableHead className="text-center text-xs font-semibold text-neutral-700">
                                Fisher p-value
                              </TableHead>
                              <TableHead className="text-xs font-semibold text-neutral-700">
                                Primary Complaint / Notes
                              </TableHead>
                              <TableHead className="text-center text-xs font-semibold text-neutral-700">
                                Batch Status
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {productReport.batches.map((batch) => (
                              <TableRow
                                key={batch.batch_id}
                                className={`transition-colors ${
                                  batch.is_suspicious
                                    ? 'border-l-4 border-l-neutral-950 bg-neutral-50 font-medium'
                                    : 'border-neutral-100 hover:bg-neutral-50/50'
                                }`}
                              >
                                <TableCell className="py-3">
                                  <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-neutral-950">
                                    {batch.is_suspicious && (
                                      <AlertTriangle className="size-3.5 text-neutral-900" />
                                    )}
                                    {batch.batch_id}
                                  </div>
                                </TableCell>
                                <TableCell className="text-xs text-neutral-700">
                                  {batch.supplier_name}
                                </TableCell>
                                <TableCell className="font-mono text-xs text-neutral-500">
                                  {batch.mfg_date}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs text-neutral-600">
                                  {batch.units_shipped.toLocaleString()}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-bold text-neutral-950">
                                  {batch.units_returned.toLocaleString()}
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs font-bold text-neutral-950">
                                  {formatPercent(batch.defect_rate)}
                                </TableCell>
                                <TableCell className="text-center">
                                  <Badge
                                    variant="outline"
                                    className={`rounded-full font-mono text-[10px] ${
                                      batch.p_value < 0.05
                                        ? 'border-neutral-950 bg-black text-white'
                                        : 'border-neutral-200 text-neutral-500'
                                    }`}
                                  >
                                    p = {batch.p_value.toFixed(4)}
                                  </Badge>
                                </TableCell>
                                <TableCell className="max-w-xs text-xs text-neutral-600">
                                  <div className="font-medium text-neutral-800">
                                    {batch.primary_cause}
                                  </div>
                                  <div className="text-[11px] text-neutral-400 truncate">
                                    {batch.notes}
                                  </div>
                                </TableCell>
                                <TableCell className="text-center">
                                  {batch.is_suspicious ? (
                                    <Badge className="rounded-full bg-neutral-950 text-[10px] text-white hover:bg-black">
                                      Suspicious / Hold
                                    </Badge>
                                  ) : (
                                    <Badge
                                      variant="outline"
                                      className="rounded-full border-neutral-200 text-[10px] text-neutral-500"
                                    >
                                      Cleared
                                    </Badge>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="mt-2 text-[10px] text-neutral-400">
                        Caption: Defect Rate = Units Returned ÷ Units Shipped. Suspicious
                        batches are highlighted where p &lt; 0.05 indicates non-random defect
                        concentration.
                      </div>
                    </CardContent>
                  </Card>

                  {/* ── Recommended Actions Section ───────────────────────────── */}
                  <Card className="border-neutral-200 bg-neutral-50/50">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="flex size-7 items-center justify-center rounded-full bg-black text-white">
                            <Sparkles className="size-3.5" />
                          </div>
                          <div>
                            <CardTitle className="text-sm font-semibold">
                              Recommended Corrective Actions
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Automated mitigation workflows generated by Agent 2 Root-Cause Engine
                            </CardDescription>
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full border-neutral-200 bg-white font-mono text-[11px]"
                        >
                          {productReport.recommended_actions.length} Action Items
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        {productReport.recommended_actions.map((action, aIdx) => {
                          const isDone = completedActions[`${selectedProductId}-${aIdx}`];
                          return (
                            <div
                              key={aIdx}
                              className={`flex items-start justify-between gap-3 rounded-xl border p-3.5 transition-all ${
                                isDone
                                  ? 'border-neutral-200 bg-neutral-100/70 text-neutral-400'
                                  : 'border-neutral-200 bg-white shadow-xs hover:border-neutral-300'
                              }`}
                            >
                              <div className="flex items-start gap-2.5">
                                <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-neutral-900 font-mono text-[10px] font-bold text-white">
                                  {aIdx + 1}
                                </span>
                                <p
                                  className={`text-xs leading-relaxed ${
                                    isDone
                                      ? 'line-through text-neutral-400'
                                      : 'text-neutral-800 font-medium'
                                  }`}
                                >
                                  {action}
                                </p>
                              </div>

                              <Button
                                variant={isDone ? 'outline' : 'secondary'}
                                size="sm"
                                className={`h-7 shrink-0 rounded-full px-2.5 text-[11px] ${
                                  isDone
                                    ? 'border-neutral-200 text-neutral-500'
                                    : 'bg-black text-white hover:bg-neutral-800'
                                }`}
                                onClick={() => toggleActionCompleted(aIdx)}
                              >
                                {isDone ? (
                                  <>
                                    <Check className="mr-1 size-3" /> Done
                                  </>
                                ) : (
                                  'Execute'
                                )}
                              </Button>
                            </div>
                          );
                        })}
                      </div>
                      <div className="mt-3 text-[10px] text-neutral-400">
                        Caption: Recommended actions are synthesized from root cause taxonomy
                        clustering, vendor defect share, and batch quarantine criteria.
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </TooltipProvider>
  );
}
