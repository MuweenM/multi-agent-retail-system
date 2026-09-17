import { useState } from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import {
  AlertTriangle,
  CheckCircle2,
  Package,
  Brain,
  Search,
  Bell,
  RefreshCw,
  ShieldAlert,
  Cpu,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Zap,
  BarChart2,
  FileSearch,
  Copy,
  Check,
  MoreHorizontal,
  Sparkles,
  CheckCircle,
  XCircle,
  HelpCircle,
  SlidersHorizontal,
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
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarBadge } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Kbd } from '@/components/ui/kbd';
import { Spinner } from '@/components/ui/spinner';
import {
  Empty,
  EmptyMedia,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from '@/components/ui/empty';
import {
  Tooltip as UiTooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

// ── Mock Datasets ─────────────────────────────────────────────────────────────

const returnVolumeData = [
  { day: 'Mon', returns: 142, resolved: 118, flagged: 24 },
  { day: 'Tue', returns: 178, resolved: 151, flagged: 27 },
  { day: 'Wed', returns: 163, resolved: 140, flagged: 23 },
  { day: 'Thu', returns: 211, resolved: 185, flagged: 26 },
  { day: 'Fri', returns: 249, resolved: 208, flagged: 41 },
  { day: 'Sat', returns: 312, resolved: 264, flagged: 48 },
  { day: 'Sun', returns: 187, resolved: 162, flagged: 25 },
];

const rootCauseData = [
  { name: 'Size / Fit Issue', value: 34, color: '#171717' },
  { name: 'Quality Defect', value: 22, color: '#525252' },
  { name: 'Wrong Item Sent', value: 18, color: '#737373' },
  { name: 'Damaged in Transit', value: 14, color: '#a3a3a3' },
  { name: 'Changed Mind', value: 12, color: '#d4d4d4' },
];

const agentActivityData = [
  { time: '00:00', intake: 12, rootcause: 10, retrieval: 9, decision: 8 },
  { time: '04:00', intake: 8, rootcause: 7, retrieval: 6, decision: 6 },
  { time: '08:00', intake: 38, rootcause: 34, retrieval: 30, decision: 28 },
  { time: '10:00', intake: 72, rootcause: 65, retrieval: 60, decision: 57 },
  { time: '12:00', intake: 95, rootcause: 87, retrieval: 82, decision: 78 },
  { time: '14:00', intake: 88, rootcause: 81, retrieval: 76, decision: 72 },
  { time: '16:00', intake: 110, rootcause: 99, retrieval: 94, decision: 90 },
  { time: '18:00', intake: 78, rootcause: 70, retrieval: 66, decision: 63 },
  { time: '20:00', intake: 45, rootcause: 40, retrieval: 37, decision: 35 },
  { time: '22:00', intake: 22, rootcause: 20, retrieval: 18, decision: 17 },
];

const confidenceTrendData = [
  { week: 'W1', confidence: 71 },
  { week: 'W2', confidence: 74 },
  { week: 'W3', confidence: 78 },
  { week: 'W4', confidence: 76 },
  { week: 'W5', confidence: 82 },
  { week: 'W6', confidence: 85 },
  { week: 'W7', confidence: 87 },
  { week: 'W8', confidence: 89 },
];

const recentReturns = [
  {
    id: 'RET-9841',
    product: 'Nike Air Max 270 – Size 10',
    customer: 'Aiden Walsh',
    initials: 'AW',
    cause: 'Size / Fit Issue',
    confidence: 94,
    status: 'approved',
    elapsed: '1m 12s',
  },
  {
    id: 'RET-9840',
    product: 'Samsung Galaxy Tab S9',
    customer: 'Priya Mehta',
    initials: 'PM',
    cause: 'Quality Defect',
    confidence: 88,
    status: 'escalated',
    elapsed: '3m 04s',
  },
  {
    id: 'RET-9839',
    product: "Levi's 501 Jeans – W32",
    customer: 'Marcus Lee',
    initials: 'ML',
    cause: 'Wrong Item Sent',
    confidence: 97,
    status: 'approved',
    elapsed: '0m 48s',
  },
  {
    id: 'RET-9838',
    product: 'Dyson V15 Vacuum',
    customer: 'Sophie Turner',
    initials: 'ST',
    cause: 'Damaged in Transit',
    confidence: 79,
    status: 'reviewing',
    elapsed: '6m 21s',
  },
  {
    id: 'RET-9837',
    product: 'Apple AirPods Pro 2',
    customer: "James O'Brien",
    initials: 'JO',
    cause: 'Changed Mind',
    confidence: 91,
    status: 'rejected',
    elapsed: '2m 33s',
  },
  {
    id: 'RET-9836',
    product: 'Adidas UltraBoost 23',
    customer: 'Yuki Tanaka',
    initials: 'YT',
    cause: 'Size / Fit Issue',
    confidence: 86,
    status: 'approved',
    elapsed: '1m 55s',
  },
];

const agentHealthData = [
  {
    id: 'A1',
    name: 'Intake Agent',
    icon: FileSearch,
    status: 'healthy',
    latency: '340ms',
    errorRate: '0.2%',
    uptime: '99.9%',
    description: 'Multi-modal returns ingest & invoice parser',
  },
  {
    id: 'A2',
    name: 'Root Cause Agent',
    icon: Brain,
    status: 'healthy',
    latency: '820ms',
    errorRate: '0.4%',
    uptime: '99.7%',
    description: 'Semantic anomaly clustering & supplier attribution',
  },
  {
    id: 'A3',
    name: 'Retrieval Agent',
    icon: Search,
    status: 'degraded',
    latency: '1.24s',
    errorRate: '1.8%',
    uptime: '97.3%',
    description: 'Vector store search & warranty policy match',
  },
  {
    id: 'A4',
    name: 'Decision Agent',
    icon: Zap,
    status: 'healthy',
    latency: '210ms',
    errorRate: '0.1%',
    uptime: '99.9%',
    description: 'Automated approval synthesis & ERP hook',
  },
];

// ── Custom Tooltip for Recharts ───────────────────────────────────────────────

function CustomChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; color: string; value: number }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-2.5 text-xs text-neutral-900 shadow-sm">
      <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-neutral-500">
        {label}
      </div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 py-0.5">
          <span
            className="inline-block h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: p.color }}
          />
          <span className="text-[11px] capitalize text-neutral-600">
            {p.name}:
          </span>
          <span className="ml-auto pl-2 font-mono font-medium text-neutral-950">
            {p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Status Badge Component ────────────────────────────────────────────────────

function ReturnStatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'approved':
      return (
        <Badge
          variant="outline"
          className="rounded-full border-emerald-200 bg-emerald-50/70 px-2.5 py-0.5 font-mono text-[10px] font-medium text-emerald-800"
        >
          <CheckCircle className="mr-1 h-3 w-3 text-emerald-600" />
          Approved
        </Badge>
      );
    case 'rejected':
      return (
        <Badge
          variant="outline"
          className="rounded-full border-rose-200 bg-rose-50/70 px-2.5 py-0.5 font-mono text-[10px] font-medium text-rose-800"
        >
          <XCircle className="mr-1 h-3 w-3 text-rose-600" />
          Rejected
        </Badge>
      );
    case 'escalated':
      return (
        <Badge
          variant="outline"
          className="rounded-full border-amber-200 bg-amber-50/70 px-2.5 py-0.5 font-mono text-[10px] font-medium text-amber-800"
        >
          <AlertTriangle className="mr-1 h-3 w-3 text-amber-600" />
          Escalated
        </Badge>
      );
    default:
      return (
        <Badge
          variant="outline"
          className="rounded-full border-neutral-200 bg-neutral-100 px-2.5 py-0.5 font-mono text-[10px] font-medium text-neutral-800"
        >
          <HelpCircle className="mr-1 h-3 w-3 text-neutral-500" />
          Reviewing
        </Badge>
      );
  }
}

// ── Main Dashboard Component ──────────────────────────────────────────────────

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [copied, setCopied] = useState(false);
  const [volumeFilter, setVolumeFilter] = useState<'7d' | '30d'>('7d');
  const [searchQuery, setSearchQuery] = useState('');
  const [policyApplied, setPolicyApplied] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const commandSnippet = `curl -X POST http://localhost:8000/api/v1/returns/simulate -d '{"sku":"NKE-270"}'`;

  const copyCommand = () => {
    navigator.clipboard.writeText(commandSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSync = () => {
    setIsSyncing(true);
    setTimeout(() => setIsSyncing(false), 1200);
  };

  const filteredReturns = recentReturns.filter(
    (r) =>
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.product.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.customer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.cause.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <TooltipProvider delayDuration={150}>
      <div className="min-h-screen bg-white font-sans text-neutral-900 antialiased selection:bg-neutral-900 selection:text-white">
        {/* ── Top Navigation Bar (Paper-white canvas, hairline border) ── */}
        <header className="sticky top-0 z-40 w-full border-b border-neutral-200 bg-white/95 backdrop-blur-sm">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            {/* Left: Brand Identity */}
            <div className="flex items-center gap-6">
              <a href="#/" className="group flex items-center gap-2.5">
                <div className="flex h-6 w-6 items-center justify-center rounded-md bg-black text-xs font-bold tracking-tight text-white">
                  R
                </div>
                <span className="text-sm font-semibold tracking-tight text-neutral-950">
                  ReturnIQ
                </span>
                <Badge
                  variant="outline"
                  className="rounded-full border-neutral-200 bg-neutral-100 px-2 py-0 font-mono text-[10px] text-neutral-600"
                >
                  v2.1
                </Badge>
              </a>

              <Separator
                orientation="vertical"
                className="hidden h-4 bg-neutral-200 sm:block"
              />

              {/* View Pill Tabs in Header using shadcn Button */}
              <nav className="hidden items-center gap-1 md:flex">
                {[
                  { id: 'overview', label: 'Overview', icon: BarChart2 },
                  { id: 'returns', label: 'Returns Queue', icon: Package },
                  { id: 'rootcause', label: 'Root Cause', icon: Brain },
                  { id: 'agents', label: 'Agent Health', icon: Cpu },
                ].map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <Button
                      key={item.id}
                      variant={isActive ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setActiveTab(item.id)}
                      className={`h-8 rounded-full px-3 text-xs font-medium shadow-none transition-all ${
                        isActive
                          ? 'bg-black text-white hover:bg-neutral-900'
                          : 'text-neutral-600 hover:bg-neutral-100 hover:text-black'
                      }`}
                    >
                      <Icon className="mr-1.5 h-3.5 w-3.5" />
                      {item.label}
                    </Button>
                  );
                })}
              </nav>
            </div>

            {/* Center / Right: Search & Actions */}
            <div className="flex items-center gap-3">
              {/* Search Pill (design.md: search-pill with shadcn Input & Kbd) */}
              <div className="relative hidden items-center lg:flex">
                <Search className="pointer-events-none absolute left-3 z-10 h-3.5 w-3.5 text-neutral-400" />
                <Input
                  type="text"
                  placeholder="Search models, returns, batch IDs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="hover:bg-neutral-150 h-8 w-64 rounded-full border-transparent bg-neutral-100 pl-8 pr-12 text-xs text-neutral-900 shadow-none transition-all focus:border-neutral-900 focus:bg-white md:w-80"
                />
                <Kbd className="pointer-events-none absolute right-2.5 text-[10px]">
                  ⌘K
                </Kbd>
              </div>

              {/* Refresh Button with shadcn Button and Spinner */}
              <UiTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleSync}
                    className="h-8 w-8 rounded-full text-neutral-500 hover:text-black"
                  >
                    {isSyncing ? (
                      <Spinner className="h-3.5 w-3.5 text-neutral-900" />
                    ) : (
                      <RefreshCw className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent className="rounded-full font-mono text-xs">
                  Sync agent stream
                </TooltipContent>
              </UiTooltip>

              {/* Notifications */}
              <UiTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="relative h-8 w-8 rounded-full text-neutral-500 hover:text-black"
                  >
                    <Bell className="h-3.5 w-3.5" />
                    <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-rose-500" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent className="rounded-full font-mono text-xs">
                  1 Degraded Agent Alert
                </TooltipContent>
              </UiTooltip>

              {/* Pure Black Primary CTA (design.md: button-primary) */}
              <Button
                size="sm"
                className="h-8 rounded-full bg-black px-4 text-xs font-medium text-white shadow-none hover:bg-neutral-800"
                onClick={() => {
                  setActiveTab('returns');
                  setSearchQuery('');
                }}
              >
                + Ingest Return
              </Button>

              {/* User Profile using shadcn Avatar, AvatarFallback, AvatarBadge */}
              <Avatar size="sm" className="border border-neutral-200">
                <AvatarFallback className="bg-neutral-100 font-mono text-[11px] font-semibold text-neutral-900">
                  LK
                </AvatarFallback>
                <AvatarBadge className="bg-emerald-500" />
              </Avatar>
            </div>
          </div>
        </header>

        {/* ── Page Main Wrap ── */}
        <main className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
          {/* ── Hero / Header Area (design.md minimal documentation style) ── */}
          <div className="flex flex-col justify-between gap-6 pb-2 md:flex-row md:items-end">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                <span className="font-mono text-[11px] uppercase tracking-widest text-neutral-500">
                  Multi-Agent Orchestration · Active
                </span>
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
                Return & Root Cause Intelligence
              </h1>
              <p className="max-w-2xl text-sm leading-relaxed text-neutral-500">
                Autonomous multi-agent orchestration across intake, root cause
                attribution, warranty retrieval, and automated refund synthesis.
              </p>
            </div>

            {/* Install / CLI Snippet Pill (design.md: install-snippet) */}
            <div className="shrink-0">
              <div className="flex items-center gap-3 rounded-full border border-neutral-200 bg-neutral-100/80 px-3.5 py-1.5">
                <span className="select-none font-mono text-[11px] text-neutral-400">
                  $
                </span>
                <code className="max-w-[280px] select-all truncate font-mono text-xs text-neutral-800 sm:max-w-none">
                  ollama run returniq-cluster
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={copyCommand}
                  className="h-6 w-6 rounded-full text-neutral-500 transition-colors hover:bg-neutral-200 hover:text-black"
                  title="Copy command"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* ── System Alert if Degraded ── */}
          <Alert className="rounded-xl border-amber-200 bg-amber-50/40 p-4 shadow-none">
            <div className="flex w-full items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <AlertTitle className="mb-0.5 text-xs font-semibold text-amber-900">
                    Degraded Subsystem: Retrieval Agent (A3)
                  </AlertTitle>
                  <AlertDescription className="text-xs text-amber-800">
                    Vector index latency spiked to 1.24s (threshold: 800ms).
                    Decision fallback agent is operating in conservative policy
                    mode.
                  </AlertDescription>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab('agents')}
                className="ml-4 h-7 shrink-0 rounded-full border-amber-300 bg-white px-3 text-xs font-medium text-amber-900 hover:bg-amber-100"
              >
                Inspect Agent
              </Button>
            </div>
          </Alert>

          {/* ── KPI Metric Strip (design.md: hairline border cards, zero shadow) ── */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Card 1: Avg Resolution Time */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none transition-colors hover:border-neutral-300">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 p-5 pb-2">
                <span className="font-mono text-xs uppercase tracking-wider text-neutral-500">
                  Avg. Resolution Time
                </span>
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-100 text-neutral-600">
                  <Clock className="h-3.5 w-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="font-mono text-2xl font-semibold tracking-tight text-neutral-950">
                  2m 18s
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className="rounded-full border-emerald-200 bg-emerald-50 px-2 py-0 font-mono text-[10px] text-emerald-700"
                  >
                    <ArrowDownRight className="mr-0.5 h-3 w-3" />
                    −34s
                  </Badge>
                  <span className="text-[11px] text-neutral-400">
                    vs. last week average
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Card 2: AI Confidence Score */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none transition-colors hover:border-neutral-300">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 p-5 pb-2">
                <span className="font-mono text-xs uppercase tracking-wider text-neutral-500">
                  AI Confidence Score
                </span>
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-100 text-neutral-600">
                  <Brain className="h-3.5 w-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="font-mono text-2xl font-semibold tracking-tight text-neutral-950">
                  87.4%
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className="rounded-full border-emerald-200 bg-emerald-50 px-2 py-0 font-mono text-[10px] text-emerald-700"
                  >
                    <ArrowUpRight className="mr-0.5 h-3 w-3" />
                    +2.1 pts
                  </Badge>
                  <span className="text-[11px] text-neutral-400">
                    attribution certainty
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Card 3: Auto-Approved Rate */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none transition-colors hover:border-neutral-300">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 p-5 pb-2">
                <span className="font-mono text-xs uppercase tracking-wider text-neutral-500">
                  Auto-Approved Rate
                </span>
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-100 text-neutral-600">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="font-mono text-2xl font-semibold tracking-tight text-neutral-950">
                  73.2%
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className="rounded-full border-emerald-200 bg-emerald-50 px-2 py-0 font-mono text-[10px] text-emerald-700"
                  >
                    <ArrowUpRight className="mr-0.5 h-3 w-3" />
                    +5.4%
                  </Badge>
                  <span className="text-[11px] text-neutral-400">
                    zero-touch resolutions
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Card 4: Anomalies Flagged (High Contrast Dark Inverted moment from design.md) */}
            <Card className="rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 p-5 pb-2">
                <span className="font-mono text-xs uppercase tracking-wider text-neutral-400">
                  Anomalies Flagged
                </span>
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-neutral-200">
                  <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="font-mono text-2xl font-semibold tracking-tight text-white">
                  48
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className="rounded-full border-amber-500/30 bg-amber-500/20 px-2 py-0 font-mono text-[10px] text-amber-300"
                  >
                    +6 today
                  </Badge>
                  <span className="text-[11px] text-neutral-400">
                    mould batch variance
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ── Main View Switching Tabs ── */}
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="space-y-6"
          >
            <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
              <TabsList className="h-9 rounded-full border border-neutral-200 bg-neutral-100 p-1">
                <TabsTrigger
                  value="overview"
                  className="rounded-full px-4 text-xs font-medium transition-all data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  Overview
                </TabsTrigger>
                <TabsTrigger
                  value="returns"
                  className="rounded-full px-4 text-xs font-medium transition-all data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  Returns Queue ({recentReturns.length})
                </TabsTrigger>
                <TabsTrigger
                  value="rootcause"
                  className="rounded-full px-4 text-xs font-medium transition-all data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  Root Cause Attribution
                </TabsTrigger>
                <TabsTrigger
                  value="agents"
                  className="rounded-full px-4 text-xs font-medium transition-all data-[state=active]:bg-black data-[state=active]:text-white"
                >
                  Agent Diagnostics
                </TabsTrigger>
              </TabsList>

              <div className="hidden items-center gap-2 sm:flex">
                <span className="text-xs text-neutral-500">
                  Live agent stream:
                </span>
                <Badge
                  variant="outline"
                  className="flex items-center gap-1 rounded-full border-emerald-200 bg-emerald-50 px-2 py-0.5 font-mono text-[10px] text-emerald-800"
                >
                  {isSyncing ? (
                    <Spinner className="h-2.5 w-2.5 text-emerald-700" />
                  ) : (
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                  )}
                  {isSyncing ? 'Syncing...' : 'In Sync'}
                </Badge>
              </div>
            </div>

            {/* ══════════════ TAB 1: OVERVIEW ══════════════ */}
            <TabsContent value="overview" className="mt-0 space-y-8">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                {/* ── Left Column (7 cols) ── */}
                <div className="space-y-6 lg:col-span-7">
                  {/* Return Volume Chart Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Return Volume & Resolution
                          </CardTitle>
                          <CardDescription className="mt-0.5 text-xs text-neutral-500">
                            7-day continuous ingest vs automated agent
                            resolution
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-1.5 rounded-full border border-neutral-200 bg-neutral-100 p-0.5">
                          <Button
                            variant={
                              volumeFilter === '7d' ? 'default' : 'ghost'
                            }
                            size="sm"
                            onClick={() => setVolumeFilter('7d')}
                            className={`h-6 rounded-full px-2.5 text-[11px] font-medium shadow-none ${
                              volumeFilter === '7d'
                                ? 'bg-black text-white hover:bg-neutral-900'
                                : 'text-neutral-600 hover:bg-neutral-200 hover:text-black'
                            }`}
                          >
                            7D
                          </Button>
                          <Button
                            variant={
                              volumeFilter === '30d' ? 'default' : 'ghost'
                            }
                            size="sm"
                            onClick={() => setVolumeFilter('30d')}
                            className={`h-6 rounded-full px-2.5 text-[11px] font-medium shadow-none ${
                              volumeFilter === '30d'
                                ? 'bg-black text-white hover:bg-neutral-900'
                                : 'text-neutral-600 hover:bg-neutral-200 hover:text-black'
                            }`}
                          >
                            30D
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="mb-4 flex items-center gap-4 font-mono text-xs text-neutral-500">
                        <div className="flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-neutral-900" />
                          <span>Returns Ingested</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-neutral-400" />
                          <span>Resolved</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                          <span>Flagged</span>
                        </div>
                      </div>
                      <div className="h-[210px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart
                            data={returnVolumeData}
                            margin={{
                              top: 10,
                              right: 10,
                              left: -20,
                              bottom: 0,
                            }}
                          >
                            <defs>
                              <linearGradient
                                id="gReturns"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                              >
                                <stop
                                  offset="5%"
                                  stopColor="#171717"
                                  stopOpacity={0.12}
                                />
                                <stop
                                  offset="95%"
                                  stopColor="#171717"
                                  stopOpacity={0.0}
                                />
                              </linearGradient>
                              <linearGradient
                                id="gResolved"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                              >
                                <stop
                                  offset="5%"
                                  stopColor="#737373"
                                  stopOpacity={0.1}
                                />
                                <stop
                                  offset="95%"
                                  stopColor="#737373"
                                  stopOpacity={0.0}
                                />
                              </linearGradient>
                            </defs>
                            <XAxis
                              dataKey="day"
                              tick={{
                                fontSize: 11,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{
                                fontSize: 11,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip content={<CustomChartTooltip />} />
                            <Area
                              type="monotone"
                              dataKey="returns"
                              stroke="#171717"
                              strokeWidth={1.75}
                              fill="url(#gReturns)"
                              dot={false}
                            />
                            <Area
                              type="monotone"
                              dataKey="resolved"
                              stroke="#737373"
                              strokeWidth={1.5}
                              fill="url(#gResolved)"
                              dot={false}
                            />
                            <Area
                              type="monotone"
                              dataKey="flagged"
                              stroke="#e11d48"
                              strokeWidth={1.5}
                              strokeDasharray="4 3"
                              fill="none"
                              dot={false}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Live Returns Queue Table Card with shadcn Avatar */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Live Returns Stream
                          </CardTitle>
                          <CardDescription className="mt-0.5 text-xs text-neutral-500">
                            Real-time pipeline across customer, cause
                            attribution, and AI status
                          </CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setActiveTab('returns')}
                          className="h-7 rounded-full border-neutral-200 px-3 text-xs font-medium shadow-none"
                        >
                          View Full Queue →
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-neutral-100 hover:bg-transparent">
                            <TableHead className="pl-5 font-mono text-[11px] text-neutral-500">
                              ID
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Customer & Product
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Root Cause
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Certainty
                            </TableHead>
                            <TableHead className="pr-5 font-mono text-[11px] text-neutral-500">
                              Status
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredReturns.slice(0, 5).map((ret) => (
                            <TableRow
                              key={ret.id}
                              className="border-neutral-100 transition-colors hover:bg-neutral-50/70"
                            >
                              <TableCell className="py-3 pl-5 font-mono text-xs font-medium text-neutral-950">
                                {ret.id}
                              </TableCell>
                              <TableCell className="py-3">
                                <div className="flex items-center gap-2.5">
                                  {/* shadcn Avatar for customer */}
                                  <Avatar
                                    size="sm"
                                    className="shrink-0 border border-neutral-200"
                                  >
                                    <AvatarFallback className="bg-neutral-100 font-mono text-[10px] font-medium text-neutral-700">
                                      {ret.initials}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div>
                                    <div className="text-xs font-medium leading-snug text-neutral-900">
                                      {ret.product}
                                    </div>
                                    <div className="text-[11px] leading-snug text-neutral-400">
                                      {ret.customer}
                                    </div>
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell className="py-3 text-xs text-neutral-600">
                                {ret.cause}
                              </TableCell>
                              <TableCell className="py-3">
                                <div className="flex max-w-[100px] items-center gap-2">
                                  <Progress
                                    value={ret.confidence}
                                    className="h-1.5 rounded-full bg-neutral-100"
                                  />
                                  <span className="min-w-[26px] font-mono text-[11px] text-neutral-500">
                                    {ret.confidence}%
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell className="py-3 pr-5">
                                <ReturnStatusBadge status={ret.status} />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  {/* Agent Activity Bar Chart Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Agent Activity & Throughput
                          </CardTitle>
                          <CardDescription className="mt-0.5 text-xs text-neutral-500">
                            Hourly throughput across intake, root cause,
                            retrieval, and decision stages
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="h-[170px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={agentActivityData}
                            margin={{
                              top: 10,
                              right: 10,
                              left: -20,
                              bottom: 0,
                            }}
                            barSize={6}
                          >
                            <XAxis
                              dataKey="time"
                              tick={{
                                fontSize: 10,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{
                                fontSize: 10,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip content={<CustomChartTooltip />} />
                            <Bar
                              dataKey="intake"
                              fill="#171717"
                              radius={[2, 2, 0, 0]}
                            />
                            <Bar
                              dataKey="rootcause"
                              fill="#525252"
                              radius={[2, 2, 0, 0]}
                            />
                            <Bar
                              dataKey="retrieval"
                              fill="#a3a3a3"
                              radius={[2, 2, 0, 0]}
                            />
                            <Bar
                              dataKey="decision"
                              fill="#d4d4d4"
                              radius={[2, 2, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* ── Right Column (5 cols) ── */}
                <div className="space-y-6 lg:col-span-5">
                  {/* AI Root Cause Anomaly Cluster (Signature Inverted Dark Card per design.md) */}
                  <Card className="relative overflow-hidden rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none">
                    <div className="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-white/5 blur-xl" />
                    <CardHeader className="p-6 pb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-amber-400" />
                          <span className="font-mono text-[11px] uppercase tracking-widest text-neutral-400">
                            Root Cause AI · Cluster
                          </span>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full border-white/20 bg-white/10 font-mono text-[10px] text-white"
                        >
                          87% Certainty
                        </Badge>
                      </div>
                      <CardTitle className="mt-3 text-lg font-semibold tracking-tight text-white">
                        Sizing Anomaly Cluster Detected
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 p-6 pt-0">
                      <p className="text-xs leading-relaxed text-neutral-300">
                        A statistically significant cluster of size-related
                        returns (↑34%) has been correlated to{' '}
                        <strong>athletic footwear SKUs</strong> over the last 72
                        hours. Root cause model traces this to{' '}
                        <strong>supplier batch mould variance</strong> (batch
                        IDs: NKE-270-BLK, NKE-270-WHT).
                      </p>

                      <div className="space-y-1.5">
                        <div className="flex justify-between font-mono text-[11px] text-neutral-400">
                          <span>Model Confidence</span>
                          <span className="font-medium text-white">
                            87% · v2.3-fine
                          </span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-800">
                          <div
                            className="h-full rounded-full bg-white transition-all duration-500"
                            style={{ width: '87%' }}
                          />
                        </div>
                      </div>

                      <div className="space-y-1 rounded-lg border border-white/10 bg-white/5 p-3 text-xs">
                        <div className="font-mono text-[10px] uppercase text-neutral-400">
                          Recommended Action
                        </div>
                        <div className="text-neutral-200">
                          Auto-approve size returns for affected SKUs & file
                          supplier batch notice within 24h.
                        </div>
                      </div>

                      {/* White Pill CTA on Dark Surface (design.md: button-pill-on-dark) */}
                      <div className="pt-1">
                        <Button
                          className={`h-9 w-full rounded-full text-xs font-semibold shadow-none transition-all ${
                            policyApplied
                              ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                              : 'bg-white text-black hover:bg-neutral-100'
                          }`}
                          onClick={() => setPolicyApplied(!policyApplied)}
                        >
                          {policyApplied ? (
                            <>
                              <Check className="mr-1.5 h-3.5 w-3.5" />
                              Auto-Approval Policy Active
                            </>
                          ) : (
                            'Apply Recommended Auto-Approval Policy'
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Root Cause Attribution Breakdown Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-2">
                      <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                        Root Cause Breakdown
                      </CardTitle>
                      <CardDescription className="mt-0.5 text-xs text-neutral-500">
                        Categorical attribution across 1,442 processed returns
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="flex items-center gap-4">
                        <div className="h-[120px] w-[120px] shrink-0">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={rootCauseData}
                                cx="50%"
                                cy="50%"
                                innerRadius={36}
                                outerRadius={54}
                                dataKey="value"
                                strokeWidth={0}
                              >
                                {rootCauseData.map((entry, idx) => (
                                  <Cell
                                    key={`cell-${idx}`}
                                    fill={entry.color}
                                  />
                                ))}
                              </Pie>
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="flex-1 space-y-2">
                          {rootCauseData.map((item) => (
                            <div
                              key={item.name}
                              className="flex items-center justify-between text-xs"
                            >
                              <div className="flex items-center gap-2">
                                <span
                                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                                  style={{ backgroundColor: item.color }}
                                />
                                <span className="text-[11px] text-neutral-700">
                                  {item.name}
                                </span>
                              </div>
                              <span className="font-mono text-[11px] font-medium text-neutral-950">
                                {item.value}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* AI Confidence 8-Week Trend Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Confidence Trajectory
                          </CardTitle>
                          <CardDescription className="mt-0.5 text-xs text-neutral-500">
                            8-week model attribution calibration
                          </CardDescription>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full border-emerald-200 bg-emerald-50 px-2 py-0.5 font-mono text-[10px] text-emerald-800"
                        >
                          ↑ +18 pts
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="h-[120px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart
                            data={confidenceTrendData}
                            margin={{
                              top: 10,
                              right: 10,
                              left: -20,
                              bottom: 0,
                            }}
                          >
                            <XAxis
                              dataKey="week"
                              tick={{
                                fontSize: 10,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              domain={[65, 95]}
                              tick={{
                                fontSize: 10,
                                fill: '#737373',
                                fontFamily: 'monospace',
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip content={<CustomChartTooltip />} />
                            <Line
                              type="monotone"
                              dataKey="confidence"
                              stroke="#171717"
                              strokeWidth={2}
                              dot={{ fill: '#171717', r: 3 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Terminal Card using shadcn Card primitives */}
                  <Card className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 text-neutral-100 shadow-none">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-neutral-800 bg-neutral-950/80 p-3">
                      {/* macOS traffic light dots */}
                      <div className="flex items-center gap-1.5">
                        <div className="h-3 w-3 rounded-full bg-[#ff5f56]" />
                        <div className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
                        <div className="h-3 w-3 rounded-full bg-[#27c93f]" />
                      </div>
                      <span className="font-mono text-[11px] text-neutral-400">
                        agent-orchestration.log
                      </span>
                      <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                    </CardHeader>
                    <CardContent className="space-y-1.5 bg-neutral-900 p-4 font-mono text-[11px] leading-relaxed text-neutral-300">
                      <div className="text-neutral-500">
                        # Multi-agent autonomous resolution trace
                      </div>
                      <div>
                        <span className="text-emerald-400">[A1:Intake]</span>{' '}
                        Ingesting RET-9841 (Nike Air Max 270)
                      </div>
                      <div>
                        <span className="text-blue-400">[A2:RootCause]</span>{' '}
                        Attribution: Size/Fit Variance (batch NKE-270)
                      </div>
                      <div>
                        <span className="text-amber-400">[A3:Retrieval]</span>{' '}
                        Policy: 30-day free size exchange (matched)
                      </div>
                      <div>
                        <span className="text-emerald-400">[A4:Decision]</span>{' '}
                        Auto-approved refund #RF-48911 ($160.00)
                      </div>
                      <div className="flex items-center gap-1 pt-1 text-neutral-500">
                        <span className="animate-pulse">_</span>
                        <span>listening on ws://localhost:8000/events</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* ══════════════ TAB 2: RETURNS QUEUE ══════════════ */}
            <TabsContent value="returns" className="mt-0 space-y-6">
              <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                <CardHeader className="p-5 pb-3">
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div>
                      <CardTitle className="text-base font-semibold tracking-tight text-neutral-950">
                        Complete Returns Inspection Queue
                      </CardTitle>
                      <CardDescription className="mt-0.5 text-xs text-neutral-500">
                        Live stream of customer return requests with AI
                        reasoning and manual override options
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 z-10 h-3.5 w-3.5 -translate-y-1/2 text-neutral-400" />
                        <Input
                          type="text"
                          placeholder="Filter queue by customer, SKU..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="h-8 w-56 rounded-full border-transparent bg-neutral-100 pl-8 pr-3 text-xs shadow-none transition-all focus:border-neutral-900 focus:bg-white"
                        />
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 rounded-full border-neutral-200 px-3 text-xs font-medium shadow-none"
                      >
                        Export CSV
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {filteredReturns.length === 0 ? (
                    <Empty className="py-12">
                      <EmptyMedia variant="icon">
                        <Package className="h-5 w-5 text-neutral-400" />
                      </EmptyMedia>
                      <EmptyHeader>
                        <EmptyTitle className="text-sm font-semibold text-neutral-900">
                          No matching returns found
                        </EmptyTitle>
                        <EmptyDescription className="text-xs text-neutral-500">
                          No return requests match &ldquo;{searchQuery}&rdquo;.
                          Try another SKU or clear the filter.
                        </EmptyDescription>
                      </EmptyHeader>
                      <EmptyContent>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSearchQuery('')}
                          className="h-7 rounded-full border-neutral-200 px-3 text-xs font-medium"
                        >
                          Clear Search
                        </Button>
                      </EmptyContent>
                    </Empty>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow className="border-neutral-100 hover:bg-transparent">
                          <TableHead className="pl-5 font-mono text-[11px] text-neutral-500">
                            Return ID
                          </TableHead>
                          <TableHead className="font-mono text-[11px] text-neutral-500">
                            Customer & Product
                          </TableHead>
                          <TableHead className="font-mono text-[11px] text-neutral-500">
                            Root Cause
                          </TableHead>
                          <TableHead className="font-mono text-[11px] text-neutral-500">
                            Certainty
                          </TableHead>
                          <TableHead className="font-mono text-[11px] text-neutral-500">
                            Time Elapsed
                          </TableHead>
                          <TableHead className="font-mono text-[11px] text-neutral-500">
                            Status
                          </TableHead>
                          <TableHead className="pr-5 text-right font-mono text-[11px] text-neutral-500">
                            Actions
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredReturns.map((ret) => (
                          <TableRow
                            key={ret.id}
                            className="border-neutral-100 transition-colors hover:bg-neutral-50/70"
                          >
                            <TableCell className="py-3.5 pl-5 font-mono text-xs font-semibold text-neutral-950">
                              {ret.id}
                            </TableCell>
                            <TableCell className="py-3.5">
                              <div className="flex items-center gap-2.5">
                                {/* Customer Avatar */}
                                <Avatar
                                  size="sm"
                                  className="shrink-0 border border-neutral-200"
                                >
                                  <AvatarFallback className="bg-neutral-100 font-mono text-[10px] font-medium text-neutral-700">
                                    {ret.initials}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <div className="text-xs font-medium leading-snug text-neutral-900">
                                    {ret.product}
                                  </div>
                                  <div className="text-[11px] leading-snug text-neutral-400">
                                    {ret.customer}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="py-3.5 text-xs text-neutral-600">
                              {ret.cause}
                            </TableCell>
                            <TableCell className="py-3.5">
                              <div className="flex max-w-[120px] items-center gap-2">
                                <Progress
                                  value={ret.confidence}
                                  className="h-1.5 rounded-full bg-neutral-100"
                                />
                                <span className="font-mono text-[11px] text-neutral-500">
                                  {ret.confidence}%
                                </span>
                              </div>
                            </TableCell>
                            <TableCell className="py-3.5 font-mono text-xs text-neutral-400">
                              {ret.elapsed}
                            </TableCell>
                            <TableCell className="py-3.5">
                              <ReturnStatusBadge status={ret.status} />
                            </TableCell>
                            <TableCell className="py-3.5 pr-5 text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 rounded-full text-neutral-400 hover:text-black"
                                  >
                                    <MoreHorizontal className="h-3.5 w-3.5" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                  align="end"
                                  className="w-44 rounded-xl"
                                >
                                  <DropdownMenuLabel className="font-mono text-[11px] uppercase text-neutral-400">
                                    Manual Override
                                  </DropdownMenuLabel>
                                  <DropdownMenuItem className="cursor-pointer text-xs">
                                    Force Auto-Approve
                                  </DropdownMenuItem>
                                  <DropdownMenuItem className="cursor-pointer text-xs">
                                    Escalate to Human Agent
                                  </DropdownMenuItem>
                                  <DropdownMenuItem className="cursor-pointer text-xs text-rose-600">
                                    Reject Return
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="cursor-pointer text-xs">
                                    Inspect Agent Trace
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* ══════════════ TAB 3: ROOT CAUSE ATTRIBUTION ══════════════ */}
            <TabsContent value="rootcause" className="mt-0 space-y-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                  <CardHeader className="p-5 pb-3">
                    <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                      Root Cause Distribution
                    </CardTitle>
                    <CardDescription className="text-xs text-neutral-500">
                      Automated classification across sizing, defect, transit,
                      and customer regret
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-5">
                    <div className="space-y-4">
                      {rootCauseData.map((item) => (
                        <div key={item.name} className="space-y-1.5">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium text-neutral-800">
                              {item.name}
                            </span>
                            <span className="font-mono text-neutral-500">
                              {item.value}%
                            </span>
                          </div>
                          <Progress
                            value={item.value}
                            className="h-2 rounded-full bg-neutral-100"
                          />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none">
                  <CardHeader className="p-5 pb-3">
                    <CardTitle className="text-sm font-semibold tracking-tight text-white">
                      Active Root Cause Insights
                    </CardTitle>
                    <CardDescription className="text-xs text-neutral-400">
                      AI identified supplier and logistics patterns
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 p-5">
                    <div className="space-y-1.5 rounded-lg border border-white/10 bg-white/5 p-3.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          Footwear Mould Discrepancy
                        </span>
                        <Badge
                          variant="outline"
                          className="rounded-full border-amber-500/30 bg-amber-500/20 font-mono text-[10px] text-amber-300"
                        >
                          High Impact
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-300">
                        Mould tool #4 at OEM facility running 0.5 size smaller
                        than standard grading. Affects SKUs NKE-270-BLK and
                        NKE-270-WHT.
                      </p>
                    </div>

                    <div className="space-y-1.5 rounded-lg border border-white/10 bg-white/5 p-3.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          Logistics Transit Shock
                        </span>
                        <Badge
                          variant="outline"
                          className="rounded-full border-neutral-500/30 bg-neutral-500/20 font-mono text-[10px] text-neutral-300"
                        >
                          Medium Impact
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-300">
                        14% damage rate on Dyson vacuums shipped via Regional
                        Route 4 (Midwest Hub). Packaging reinforcement
                        recommended.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* ══════════════ TAB 4: AGENT DIAGNOSTICS ══════════════ */}
            <TabsContent value="agents" className="mt-0 space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {agentHealthData.map((agent) => {
                  const Icon = agent.icon;
                  const isDegraded = agent.status === 'degraded';
                  return (
                    <Card
                      key={agent.id}
                      className={`rounded-xl border shadow-none transition-colors ${
                        isDegraded
                          ? 'border-amber-300 bg-amber-50/20'
                          : 'border-neutral-200 bg-white hover:border-neutral-300'
                      }`}
                    >
                      <CardHeader className="p-5 pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            {/* Agent Avatar with status badge */}
                            <Avatar
                              size="default"
                              className="shrink-0 border border-neutral-200"
                            >
                              <AvatarFallback
                                className={
                                  isDegraded
                                    ? 'bg-amber-100 text-amber-900'
                                    : 'bg-neutral-100 text-neutral-900'
                                }
                              >
                                <Icon className="h-3.5 w-3.5" />
                              </AvatarFallback>
                              <AvatarBadge
                                className={
                                  isDegraded ? 'bg-amber-500' : 'bg-emerald-500'
                                }
                              />
                            </Avatar>
                            <div>
                              <div className="text-xs font-semibold text-neutral-950">
                                {agent.name}
                              </div>
                              <div className="font-mono text-[10px] text-neutral-400">
                                Agent {agent.id}
                              </div>
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-medium ${
                              isDegraded
                                ? 'border-amber-300 bg-amber-100 text-amber-900'
                                : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                            }`}
                          >
                            {isDegraded ? '⚠ Degraded' : '● Healthy'}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3 p-5 pt-0">
                        <p className="min-h-[32px] text-[11px] leading-normal text-neutral-500">
                          {agent.description}
                        </p>
                        <Separator className="bg-neutral-100" />
                        <div className="grid grid-cols-3 gap-2 pt-1 text-center font-mono">
                          <div>
                            <div className="mb-0.5 text-[9px] uppercase text-neutral-400">
                              Latency
                            </div>
                            <div
                              className={`text-xs font-medium ${
                                isDegraded
                                  ? 'text-amber-700'
                                  : 'text-neutral-900'
                              }`}
                            >
                              {agent.latency}
                            </div>
                          </div>
                          <div>
                            <div className="mb-0.5 text-[9px] uppercase text-neutral-400">
                              Errors
                            </div>
                            <div
                              className={`text-xs font-medium ${
                                isDegraded
                                  ? 'text-amber-700'
                                  : 'text-neutral-900'
                              }`}
                            >
                              {agent.errorRate}
                            </div>
                          </div>
                          <div>
                            <div className="mb-0.5 text-[9px] uppercase text-neutral-400">
                              Uptime
                            </div>
                            <div className="text-xs font-medium text-neutral-900">
                              {agent.uptime}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
          </Tabs>

          {/* ── Agent Health Strip (Bottom Persistent) ── */}
          <div className="border-t border-neutral-200 pt-4">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div className="flex items-center gap-3">
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium text-neutral-800">
                  Cluster Status: 3 Operational · 1 Degraded
                </span>
                <span className="text-neutral-300">|</span>
                <span className="font-mono text-xs text-neutral-400">
                  ReturnIQ Cluster v2.1.0 · LLM Backend: GPT-4o
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="rounded-full border-neutral-200 bg-neutral-100 px-2.5 py-0.5 font-mono text-[10px] text-neutral-600"
                >
                  <SlidersHorizontal className="mr-1 h-3 w-3 text-neutral-400" />
                  Policy Autonomy: L3 Supervised
                </Badge>
              </div>
            </div>
          </div>
        </main>
      </div>
    </TooltipProvider>
  );
}
