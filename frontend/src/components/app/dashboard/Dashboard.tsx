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
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
    cause: 'Size / Fit Issue',
    confidence: 94,
    status: 'approved',
    elapsed: '1m 12s',
  },
  {
    id: 'RET-9840',
    product: 'Samsung Galaxy Tab S9',
    customer: 'Priya Mehta',
    cause: 'Quality Defect',
    confidence: 88,
    status: 'escalated',
    elapsed: '3m 04s',
  },
  {
    id: 'RET-9839',
    product: "Levi's 501 Jeans – W32",
    customer: 'Marcus Lee',
    cause: 'Wrong Item Sent',
    confidence: 97,
    status: 'approved',
    elapsed: '0m 48s',
  },
  {
    id: 'RET-9838',
    product: 'Dyson V15 Vacuum',
    customer: 'Sophie Turner',
    cause: 'Damaged in Transit',
    confidence: 79,
    status: 'reviewing',
    elapsed: '6m 21s',
  },
  {
    id: 'RET-9837',
    product: 'Apple AirPods Pro 2',
    customer: "James O'Brien",
    cause: 'Changed Mind',
    confidence: 91,
    status: 'rejected',
    elapsed: '2m 33s',
  },
  {
    id: 'RET-9836',
    product: 'Adidas UltraBoost 23',
    customer: 'Yuki Tanaka',
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
      <div className="font-mono text-[10px] text-neutral-500 mb-1.5 uppercase tracking-wider">
        {label}
      </div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 py-0.5">
          <span
            className="w-2 h-2 rounded-full inline-block shrink-0"
            style={{ backgroundColor: p.color }}
          />
          <span className="text-neutral-600 capitalize text-[11px]">{p.name}:</span>
          <span className="font-mono font-medium ml-auto pl-2 text-neutral-950">{p.value}</span>
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
          className="rounded-full bg-emerald-50/70 text-emerald-800 border-emerald-200 text-[10px] font-mono font-medium px-2.5 py-0.5"
        >
          <CheckCircle className="w-3 h-3 mr-1 text-emerald-600" />
          Approved
        </Badge>
      );
    case 'rejected':
      return (
        <Badge
          variant="outline"
          className="rounded-full bg-rose-50/70 text-rose-800 border-rose-200 text-[10px] font-mono font-medium px-2.5 py-0.5"
        >
          <XCircle className="w-3 h-3 mr-1 text-rose-600" />
          Rejected
        </Badge>
      );
    case 'escalated':
      return (
        <Badge
          variant="outline"
          className="rounded-full bg-amber-50/70 text-amber-800 border-amber-200 text-[10px] font-mono font-medium px-2.5 py-0.5"
        >
          <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />
          Escalated
        </Badge>
      );
    default:
      return (
        <Badge
          variant="outline"
          className="rounded-full bg-neutral-100 text-neutral-800 border-neutral-200 text-[10px] font-mono font-medium px-2.5 py-0.5"
        >
          <HelpCircle className="w-3 h-3 mr-1 text-neutral-500" />
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

  const commandSnippet = `curl -X POST http://localhost:8000/api/v1/returns/simulate -d '{"sku":"NKE-270"}'`;

  const copyCommand = () => {
    navigator.clipboard.writeText(commandSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
      <div className="min-h-screen bg-white text-neutral-900 font-sans antialiased selection:bg-neutral-900 selection:text-white">
        {/* ── Top Navigation Bar (Paper-white canvas, hairline border) ── */}
        <header className="sticky top-0 z-40 w-full border-b border-neutral-200 bg-white/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
            {/* Left: Brand Identity */}
            <div className="flex items-center gap-6">
              <a href="#/" className="flex items-center gap-2.5 group">
                <div className="w-6 h-6 rounded-md bg-black text-white flex items-center justify-center font-bold text-xs tracking-tight">
                  R
                </div>
                <span className="font-semibold text-sm tracking-tight text-neutral-950">
                  ReturnIQ
                </span>
                <Badge
                  variant="outline"
                  className="rounded-full bg-neutral-100 text-neutral-600 border-neutral-200 text-[10px] font-mono px-2 py-0"
                >
                  v2.1
                </Badge>
              </a>

              <Separator orientation="vertical" className="h-4 bg-neutral-200 hidden sm:block" />

              {/* View Pill Tabs in Header */}
              <nav className="hidden md:flex items-center gap-1">
                {[
                  { id: 'overview', label: 'Overview', icon: BarChart2 },
                  { id: 'returns', label: 'Returns Queue', icon: Package },
                  { id: 'rootcause', label: 'Root Cause', icon: Brain },
                  { id: 'agents', label: 'Agent Health', icon: Cpu },
                ].map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                        isActive
                          ? 'bg-black text-white'
                          : 'text-neutral-600 hover:text-black hover:bg-neutral-100'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Center / Right: Search & Actions */}
            <div className="flex items-center gap-3">
              {/* Search Pill (design.md: search-pill) */}
              <div className="relative hidden lg:flex items-center">
                <Search className="w-3.5 h-3.5 absolute left-3 text-neutral-400 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search models, returns, batch IDs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="rounded-full bg-neutral-100 hover:bg-neutral-150 focus:bg-white border border-transparent focus:border-neutral-900 focus:outline-none text-xs text-neutral-900 pl-8 pr-12 py-1.5 w-64 transition-all"
                />
                <kbd className="absolute right-2.5 text-[10px] font-mono text-neutral-400 bg-neutral-200/60 rounded px-1.5 py-0.5 pointer-events-none">
                  ⌘K
                </kbd>
              </div>

              {/* Refresh Button */}
              <UiTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full w-8 h-8 text-neutral-500 hover:text-black"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent className="rounded-full text-xs font-mono">
                  Sync agent stream
                </TooltipContent>
              </UiTooltip>

              {/* Notifications */}
              <UiTooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full w-8 h-8 text-neutral-500 hover:text-black relative"
                  >
                    <Bell className="w-3.5 h-3.5" />
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 absolute top-1.5 right-1.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent className="rounded-full text-xs font-mono">
                  1 Degraded Agent Alert
                </TooltipContent>
              </UiTooltip>

              {/* Pure Black Primary CTA (design.md: button-primary) */}
              <Button
                size="sm"
                className="rounded-full bg-black text-white hover:bg-neutral-800 text-xs px-4 h-8 font-medium shadow-none"
                onClick={() => {
                  setActiveTab('returns');
                  setSearchQuery('');
                }}
              >
                + Ingest Return
              </Button>

              {/* User Avatar */}
              <Avatar className="w-7 h-7 rounded-full border border-neutral-200">
                <AvatarFallback className="bg-neutral-100 text-neutral-800 text-[11px] font-medium">
                  LK
                </AvatarFallback>
              </Avatar>
            </div>
          </div>
        </header>

        {/* ── Page Main Wrap ── */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {/* ── Hero / Header Area (design.md minimal documentation style) ── */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-500">
                  Multi-Agent Orchestration · Active
                </span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-neutral-950">
                Return & Root Cause Intelligence
              </h1>
              <p className="text-sm text-neutral-500 max-w-2xl leading-relaxed">
                Autonomous multi-agent orchestration across intake, root cause attribution, warranty
                retrieval, and automated refund synthesis.
              </p>
            </div>

            {/* Install / CLI Snippet Pill (design.md: install-snippet) */}
            <div className="shrink-0">
              <div className="rounded-full bg-neutral-100/80 border border-neutral-200 px-3.5 py-1.5 flex items-center gap-3">
                <span className="text-[11px] font-mono text-neutral-400 select-none">$</span>
                <code className="text-xs font-mono text-neutral-800 select-all max-w-[280px] sm:max-w-none truncate">
                  ollama run returniq-cluster
                </code>
                <button
                  onClick={copyCommand}
                  className="text-neutral-500 hover:text-black p-1 rounded-full hover:bg-neutral-200 transition-colors"
                  title="Copy command"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* ── System Alert if Degraded ── */}
          <Alert className="rounded-xl border-amber-200 bg-amber-50/40 p-4 shadow-none">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                <div>
                  <AlertTitle className="text-xs font-semibold text-amber-900 mb-0.5">
                    Degraded Subsystem: Retrieval Agent (A3)
                  </AlertTitle>
                  <AlertDescription className="text-xs text-amber-800">
                    Vector index latency spiked to 1.24s (threshold: 800ms). Decision fallback agent
                    is operating in conservative policy mode.
                  </AlertDescription>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab('agents')}
                className="rounded-full bg-white border-amber-300 text-amber-900 hover:bg-amber-100 text-xs h-7 px-3 ml-4 shrink-0 font-medium"
              >
                Inspect Agent
              </Button>
            </div>
          </Alert>

          {/* ── KPI Metric Strip (design.md: hairline border cards, zero shadow) ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Avg Resolution Time */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none hover:border-neutral-300 transition-colors">
              <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-500">
                  Avg. Resolution Time
                </span>
                <div className="w-7 h-7 rounded-full bg-neutral-100 flex items-center justify-center text-neutral-600">
                  <Clock className="w-3.5 h-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="text-2xl font-semibold tracking-tight text-neutral-950 font-mono">
                  2m 18s
                </div>
                <div className="flex items-center gap-1.5 mt-2">
                  <Badge
                    variant="outline"
                    className="rounded-full bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] font-mono px-2 py-0"
                  >
                    <ArrowDownRight className="w-3 h-3 mr-0.5" />
                    −34s
                  </Badge>
                  <span className="text-[11px] text-neutral-400">vs. last week average</span>
                </div>
              </CardContent>
            </Card>

            {/* Card 2: AI Confidence Score */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none hover:border-neutral-300 transition-colors">
              <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-500">
                  AI Confidence Score
                </span>
                <div className="w-7 h-7 rounded-full bg-neutral-100 flex items-center justify-center text-neutral-600">
                  <Brain className="w-3.5 h-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="text-2xl font-semibold tracking-tight text-neutral-950 font-mono">
                  87.4%
                </div>
                <div className="flex items-center gap-1.5 mt-2">
                  <Badge
                    variant="outline"
                    className="rounded-full bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] font-mono px-2 py-0"
                  >
                    <ArrowUpRight className="w-3 h-3 mr-0.5" />
                    +2.1 pts
                  </Badge>
                  <span className="text-[11px] text-neutral-400">attribution certainty</span>
                </div>
              </CardContent>
            </Card>

            {/* Card 3: Auto-Approved Rate */}
            <Card className="rounded-xl border border-neutral-200 bg-white shadow-none hover:border-neutral-300 transition-colors">
              <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-500">
                  Auto-Approved Rate
                </span>
                <div className="w-7 h-7 rounded-full bg-neutral-100 flex items-center justify-center text-neutral-600">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="text-2xl font-semibold tracking-tight text-neutral-950 font-mono">
                  73.2%
                </div>
                <div className="flex items-center gap-1.5 mt-2">
                  <Badge
                    variant="outline"
                    className="rounded-full bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] font-mono px-2 py-0"
                  >
                    <ArrowUpRight className="w-3 h-3 mr-0.5" />
                    +5.4%
                  </Badge>
                  <span className="text-[11px] text-neutral-400">zero-touch resolutions</span>
                </div>
              </CardContent>
            </Card>

            {/* Card 4: Anomalies Flagged (High Contrast Dark Inverted moment from design.md) */}
            <Card className="rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none">
              <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-400">
                  Anomalies Flagged
                </span>
                <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-neutral-200">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <div className="text-2xl font-semibold tracking-tight text-white font-mono">
                  48
                </div>
                <div className="flex items-center gap-1.5 mt-2">
                  <Badge
                    variant="outline"
                    className="rounded-full bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] font-mono px-2 py-0"
                  >
                    +6 today
                  </Badge>
                  <span className="text-[11px] text-neutral-400">mould batch variance</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ── Main View Switching Tabs ── */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
              <TabsList className="bg-neutral-100 rounded-full p-1 border border-neutral-200 h-9">
                <TabsTrigger
                  value="overview"
                  className="rounded-full px-4 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white transition-all"
                >
                  Overview
                </TabsTrigger>
                <TabsTrigger
                  value="returns"
                  className="rounded-full px-4 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white transition-all"
                >
                  Returns Queue ({recentReturns.length})
                </TabsTrigger>
                <TabsTrigger
                  value="rootcause"
                  className="rounded-full px-4 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white transition-all"
                >
                  Root Cause Attribution
                </TabsTrigger>
                <TabsTrigger
                  value="agents"
                  className="rounded-full px-4 text-xs font-medium data-[state=active]:bg-black data-[state=active]:text-white transition-all"
                >
                  Agent Diagnostics
                </TabsTrigger>
              </TabsList>

              <div className="hidden sm:flex items-center gap-2">
                <span className="text-xs text-neutral-500">Live agent stream:</span>
                <Badge
                  variant="outline"
                  className="rounded-full bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px] font-mono px-2 py-0.5"
                >
                  ● In Sync
                </Badge>
              </div>
            </div>

            {/* ══════════════ TAB 1: OVERVIEW ══════════════ */}
            <TabsContent value="overview" className="space-y-8 mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* ── Left Column (7 cols) ── */}
                <div className="lg:col-span-7 space-y-6">
                  {/* Return Volume Chart Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Return Volume & Resolution
                          </CardTitle>
                          <CardDescription className="text-xs text-neutral-500 mt-0.5">
                            7-day continuous ingest vs automated agent resolution
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setVolumeFilter('7d')}
                            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
                              volumeFilter === '7d'
                                ? 'bg-black text-white'
                                : 'text-neutral-500 hover:text-black bg-neutral-100'
                            }`}
                          >
                            7D
                          </button>
                          <button
                            onClick={() => setVolumeFilter('30d')}
                            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
                              volumeFilter === '30d'
                                ? 'bg-black text-white'
                                : 'text-neutral-500 hover:text-black bg-neutral-100'
                            }`}
                          >
                            30D
                          </button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="flex items-center gap-4 text-xs text-neutral-500 mb-4 font-mono">
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-neutral-900" />
                          <span>Returns Ingested</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-neutral-400" />
                          <span>Resolved</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                          <span>Flagged</span>
                        </div>
                      </div>
                      <div className="h-[210px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart
                            data={returnVolumeData}
                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                          >
                            <defs>
                              <linearGradient id="gReturns" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#171717" stopOpacity={0.12} />
                                <stop offset="95%" stopColor="#171717" stopOpacity={0.0} />
                              </linearGradient>
                              <linearGradient id="gResolved" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#737373" stopOpacity={0.1} />
                                <stop offset="95%" stopColor="#737373" stopOpacity={0.0} />
                              </linearGradient>
                            </defs>
                            <XAxis
                              dataKey="day"
                              tick={{ fontSize: 11, fill: '#737373', fontFamily: 'monospace' }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{ fontSize: 11, fill: '#737373', fontFamily: 'monospace' }}
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

                  {/* Live Returns Queue Table Card */}
                  <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                            Live Returns Stream
                          </CardTitle>
                          <CardDescription className="text-xs text-neutral-500 mt-0.5">
                            Real-time pipeline across customer, cause attribution, and AI status
                          </CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setActiveTab('returns')}
                          className="rounded-full text-xs h-7 px-3 border-neutral-200 font-medium"
                        >
                          View Full Queue →
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-neutral-100 hover:bg-transparent">
                            <TableHead className="font-mono text-[11px] text-neutral-500 pl-5">
                              ID
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Product / Customer
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Root Cause
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500">
                              Certainty
                            </TableHead>
                            <TableHead className="font-mono text-[11px] text-neutral-500 pr-5">
                              Status
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredReturns.slice(0, 5).map((ret) => (
                            <TableRow
                              key={ret.id}
                              className="border-neutral-100 hover:bg-neutral-50/70 transition-colors"
                            >
                              <TableCell className="font-mono text-xs font-medium text-neutral-950 pl-5 py-3">
                                {ret.id}
                              </TableCell>
                              <TableCell className="py-3">
                                <div className="text-xs font-medium text-neutral-900">
                                  {ret.product}
                                </div>
                                <div className="text-[11px] text-neutral-400">{ret.customer}</div>
                              </TableCell>
                              <TableCell className="text-xs text-neutral-600 py-3">
                                {ret.cause}
                              </TableCell>
                              <TableCell className="py-3">
                                <div className="flex items-center gap-2 max-w-[100px]">
                                  <Progress
                                    value={ret.confidence}
                                    className="h-1.5 rounded-full bg-neutral-100"
                                  />
                                  <span className="font-mono text-[11px] text-neutral-500 min-w-[26px]">
                                    {ret.confidence}%
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell className="pr-5 py-3">
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
                          <CardDescription className="text-xs text-neutral-500 mt-0.5">
                            Hourly throughput across intake, root cause, retrieval, and decision
                            stages
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="h-[170px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={agentActivityData}
                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                            barSize={6}
                          >
                            <XAxis
                              dataKey="time"
                              tick={{ fontSize: 10, fill: '#737373', fontFamily: 'monospace' }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{ fontSize: 10, fill: '#737373', fontFamily: 'monospace' }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip content={<CustomChartTooltip />} />
                            <Bar dataKey="intake" fill="#171717" radius={[2, 2, 0, 0]} />
                            <Bar dataKey="rootcause" fill="#525252" radius={[2, 2, 0, 0]} />
                            <Bar dataKey="retrieval" fill="#a3a3a3" radius={[2, 2, 0, 0]} />
                            <Bar dataKey="decision" fill="#d4d4d4" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* ── Right Column (5 cols) ── */}
                <div className="lg:col-span-5 space-y-6">
                  {/* AI Root Cause Anomaly Cluster (Signature Inverted Dark Card per design.md) */}
                  <Card className="rounded-xl border border-neutral-800 bg-[#171717] text-white shadow-none relative overflow-hidden">
                    <div className="absolute -top-12 -right-12 w-36 h-36 rounded-full bg-white/5 pointer-events-none blur-xl" />
                    <CardHeader className="p-6 pb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-amber-400" />
                          <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                            Root Cause AI · Cluster
                          </span>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full bg-white/10 text-white border-white/20 text-[10px] font-mono"
                        >
                          87% Certainty
                        </Badge>
                      </div>
                      <CardTitle className="text-lg font-semibold tracking-tight text-white mt-3">
                        Sizing Anomaly Cluster Detected
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6 pt-0 space-y-4">
                      <p className="text-xs text-neutral-300 leading-relaxed">
                        A statistically significant cluster of size-related returns (↑34%) has been
                        correlated to <strong>athletic footwear SKUs</strong> over the last 72
                        hours. Root cause model traces this to{' '}
                        <strong>supplier batch mould variance</strong> (batch IDs: NKE-270-BLK,
                        NKE-270-WHT).
                      </p>

                      <div className="space-y-1.5">
                        <div className="flex justify-between text-[11px] font-mono text-neutral-400">
                          <span>Model Confidence</span>
                          <span className="text-white font-medium">87% · v2.3-fine</span>
                        </div>
                        <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-white h-full rounded-full transition-all duration-500"
                            style={{ width: '87%' }}
                          />
                        </div>
                      </div>

                      <div className="rounded-lg bg-white/5 border border-white/10 p-3 text-xs space-y-1">
                        <div className="font-mono text-[10px] uppercase text-neutral-400">
                          Recommended Action
                        </div>
                        <div className="text-neutral-200">
                          Auto-approve size returns for affected SKUs & file supplier batch notice
                          within 24h.
                        </div>
                      </div>

                      {/* White Pill CTA on Dark Surface (design.md: button-pill-on-dark) */}
                      <div className="pt-1">
                        <Button
                          className={`w-full rounded-full text-xs font-semibold h-9 shadow-none transition-all ${
                            policyApplied
                              ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                              : 'bg-white text-black hover:bg-neutral-100'
                          }`}
                          onClick={() => setPolicyApplied(!policyApplied)}
                        >
                          {policyApplied ? (
                            <>
                              <Check className="w-3.5 h-3.5 mr-1.5" />
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
                      <CardDescription className="text-xs text-neutral-500 mt-0.5">
                        Categorical attribution across 1,442 processed returns
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <div className="flex items-center gap-4">
                        <div className="w-[120px] h-[120px] shrink-0">
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
                                  <Cell key={`cell-${idx}`} fill={entry.color} />
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
                                  className="w-2.5 h-2.5 rounded-full shrink-0"
                                  style={{ backgroundColor: item.color }}
                                />
                                <span className="text-neutral-700 text-[11px]">{item.name}</span>
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
                          <CardDescription className="text-xs text-neutral-500 mt-0.5">
                            8-week model attribution calibration
                          </CardDescription>
                        </div>
                        <Badge
                          variant="outline"
                          className="rounded-full bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px] font-mono px-2 py-0.5"
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
                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                          >
                            <XAxis
                              dataKey="week"
                              tick={{ fontSize: 10, fill: '#737373', fontFamily: 'monospace' }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              domain={[65, 95]}
                              tick={{ fontSize: 10, fill: '#737373', fontFamily: 'monospace' }}
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

                  {/* Terminal Card (macOS Traffic Light Dots per design.md) */}
                  <Card className="rounded-xl border border-neutral-200 bg-neutral-900 text-neutral-100 shadow-none overflow-hidden">
                    <div className="p-3 bg-neutral-950/80 border-b border-neutral-800 flex items-center justify-between">
                      {/* macOS traffic light dots */}
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                        <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                        <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                      </div>
                      <span className="text-[11px] font-mono text-neutral-400">
                        agent-orchestration.log
                      </span>
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    </div>
                    <div className="p-4 font-mono text-[11px] text-neutral-300 space-y-1.5 leading-relaxed bg-neutral-900">
                      <div className="text-neutral-500">
                        # Multi-agent autonomous resolution trace
                      </div>
                      <div>
                        <span className="text-emerald-400">[A1:Intake]</span> Ingesting RET-9841
                        (Nike Air Max 270)
                      </div>
                      <div>
                        <span className="text-blue-400">[A2:RootCause]</span> Attribution: Size/Fit
                        Variance (batch NKE-270)
                      </div>
                      <div>
                        <span className="text-amber-400">[A3:Retrieval]</span> Policy: 30-day free
                        size exchange (matched)
                      </div>
                      <div>
                        <span className="text-emerald-400">[A4:Decision]</span> Auto-approved refund
                        #RF-48911 ($160.00)
                      </div>
                      <div className="text-neutral-500 pt-1 flex items-center gap-1">
                        <span className="animate-pulse">_</span>
                        <span>listening on ws://localhost:8000/events</span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* ══════════════ TAB 2: RETURNS QUEUE ══════════════ */}
            <TabsContent value="returns" className="space-y-6 mt-0">
              <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                <CardHeader className="p-5 pb-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <CardTitle className="text-base font-semibold tracking-tight text-neutral-950">
                        Complete Returns Inspection Queue
                      </CardTitle>
                      <CardDescription className="text-xs text-neutral-500 mt-0.5">
                        Live stream of customer return requests with AI reasoning and manual
                        override options
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                        <input
                          type="text"
                          placeholder="Filter queue..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="rounded-full bg-neutral-100 border border-transparent focus:border-neutral-900 focus:bg-white text-xs pl-8 pr-3 py-1.5 w-48 transition-all"
                        />
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="rounded-full text-xs h-8 px-3 border-neutral-200 font-medium"
                      >
                        Export CSV
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-neutral-100 hover:bg-transparent">
                        <TableHead className="font-mono text-[11px] text-neutral-500 pl-5">
                          Return ID
                        </TableHead>
                        <TableHead className="font-mono text-[11px] text-neutral-500">
                          Product
                        </TableHead>
                        <TableHead className="font-mono text-[11px] text-neutral-500">
                          Customer
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
                        <TableHead className="font-mono text-[11px] text-neutral-500 pr-5 text-right">
                          Actions
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredReturns.map((ret) => (
                        <TableRow
                          key={ret.id}
                          className="border-neutral-100 hover:bg-neutral-50/70 transition-colors"
                        >
                          <TableCell className="font-mono text-xs font-semibold text-neutral-950 pl-5 py-3.5">
                            {ret.id}
                          </TableCell>
                          <TableCell className="text-xs font-medium text-neutral-900 py-3.5">
                            {ret.product}
                          </TableCell>
                          <TableCell className="text-xs text-neutral-500 py-3.5">
                            {ret.customer}
                          </TableCell>
                          <TableCell className="text-xs text-neutral-600 py-3.5">
                            {ret.cause}
                          </TableCell>
                          <TableCell className="py-3.5">
                            <div className="flex items-center gap-2 max-w-[120px]">
                              <Progress
                                value={ret.confidence}
                                className="h-1.5 rounded-full bg-neutral-100"
                              />
                              <span className="font-mono text-[11px] text-neutral-500">
                                {ret.confidence}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-neutral-400 py-3.5">
                            {ret.elapsed}
                          </TableCell>
                          <TableCell className="py-3.5">
                            <ReturnStatusBadge status={ret.status} />
                          </TableCell>
                          <TableCell className="pr-5 py-3.5 text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="w-7 h-7 rounded-full text-neutral-400 hover:text-black"
                                >
                                  <MoreHorizontal className="w-3.5 h-3.5" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="rounded-xl w-44">
                                <DropdownMenuLabel className="text-[11px] font-mono uppercase text-neutral-400">
                                  Manual Override
                                </DropdownMenuLabel>
                                <DropdownMenuItem className="text-xs cursor-pointer">
                                  Force Auto-Approve
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-xs cursor-pointer">
                                  Escalate to Human Agent
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-xs cursor-pointer text-rose-600">
                                  Reject Return
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-xs cursor-pointer">
                                  Inspect Agent Trace
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* ══════════════ TAB 3: ROOT CAUSE ATTRIBUTION ══════════════ */}
            <TabsContent value="rootcause" className="space-y-6 mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
                  <CardHeader className="p-5 pb-3">
                    <CardTitle className="text-sm font-semibold tracking-tight text-neutral-950">
                      Root Cause Distribution
                    </CardTitle>
                    <CardDescription className="text-xs text-neutral-500">
                      Automated classification across sizing, defect, transit, and customer regret
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-5">
                    <div className="space-y-4">
                      {rootCauseData.map((item) => (
                        <div key={item.name} className="space-y-1.5">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium text-neutral-800">{item.name}</span>
                            <span className="font-mono text-neutral-500">{item.value}%</span>
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
                  <CardContent className="p-5 space-y-4">
                    <div className="p-3.5 rounded-lg bg-white/5 border border-white/10 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          Footwear Mould Discrepancy
                        </span>
                        <Badge
                          variant="outline"
                          className="rounded-full bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px] font-mono"
                        >
                          High Impact
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-300">
                        Mould tool #4 at OEM facility running 0.5 size smaller than standard
                        grading. Affects SKUs NKE-270-BLK and NKE-270-WHT.
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-white/5 border border-white/10 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          Logistics Transit Shock
                        </span>
                        <Badge
                          variant="outline"
                          className="rounded-full bg-neutral-500/20 text-neutral-300 border-neutral-500/30 text-[10px] font-mono"
                        >
                          Medium Impact
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-300">
                        14% damage rate on Dyson vacuums shipped via Regional Route 4 (Midwest Hub).
                        Packaging reinforcement recommended.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* ══════════════ TAB 4: AGENT DIAGNOSTICS ══════════════ */}
            <TabsContent value="agents" className="space-y-6 mt-0">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
                          <div className="flex items-center gap-2">
                            <div
                              className={`w-7 h-7 rounded-md flex items-center justify-center ${
                                isDegraded
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-neutral-100 text-neutral-800'
                              }`}
                            >
                              <Icon className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-neutral-950">
                                {agent.name}
                              </div>
                              <div className="text-[10px] font-mono text-neutral-400">
                                Agent {agent.id}
                              </div>
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className={`rounded-full text-[10px] font-mono font-medium px-2 py-0.5 ${
                              isDegraded
                                ? 'bg-amber-100 text-amber-900 border-amber-300'
                                : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            }`}
                          >
                            {isDegraded ? '⚠ Degraded' : '● Healthy'}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="p-5 pt-0 space-y-3">
                        <p className="text-[11px] text-neutral-500 leading-normal min-h-[32px]">
                          {agent.description}
                        </p>
                        <Separator className="bg-neutral-100" />
                        <div className="grid grid-cols-3 gap-2 font-mono text-center pt-1">
                          <div>
                            <div className="text-[9px] uppercase text-neutral-400 mb-0.5">
                              Latency
                            </div>
                            <div
                              className={`text-xs font-medium ${
                                isDegraded ? 'text-amber-700' : 'text-neutral-900'
                              }`}
                            >
                              {agent.latency}
                            </div>
                          </div>
                          <div>
                            <div className="text-[9px] uppercase text-neutral-400 mb-0.5">
                              Errors
                            </div>
                            <div
                              className={`text-xs font-medium ${
                                isDegraded ? 'text-amber-700' : 'text-neutral-900'
                              }`}
                            >
                              {agent.errorRate}
                            </div>
                          </div>
                          <div>
                            <div className="text-[9px] uppercase text-neutral-400 mb-0.5">
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
          <div className="pt-4 border-t border-neutral-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium text-neutral-800">
                  Cluster Status: 3 Operational · 1 Degraded
                </span>
                <span className="text-neutral-300">|</span>
                <span className="font-mono text-xs text-neutral-400">
                  ReturnIQ Cluster v2.1.0 · LLM Backend: GPT-4o
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </TooltipProvider>
  );
}
