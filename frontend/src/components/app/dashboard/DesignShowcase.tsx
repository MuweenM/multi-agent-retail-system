import { useState } from 'react';
import { motion } from 'framer-motion';

// ── shadcn/ui components ──────────────────────────────────────────────────────
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardAction,
} from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { Toggle } from '@/components/ui/toggle';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Kbd } from '@/components/ui/kbd';
import {
  Empty,
  EmptyMedia,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from '@/components/ui/empty';
import { Bubble } from '@/components/ui/bubble';

// ── Lucide icons ──────────────────────────────────────────────────────────────
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Cpu,
  FileSearch,
  Info,
  LayoutDashboard,
  Lock,
  MoreHorizontal,
  Package,
  RefreshCw,
  Search,
  Settings,
  ShieldAlert,
  Terminal,
  Trash2,
  User,
  Zap,
  Grid3x3,
  PanelLeft,
  List,
  AlignLeft,
  Bold,
  Italic,
  Underline,
} from 'lucide-react';

// ─── Shared token colours (from design.md) ───────────────────────────────────
const COLORS = {
  primary: '#000000',
  canvas: '#ffffff',
  surfaceSoft: '#fafafa',
  surfaceDark: '#171717',
  hairline: '#e5e5e5',
  hairlineStrong: '#d4d4d4',
  body: '#737373',
  charcoal: '#525252',
  mute: '#a3a3a3',
  termRed: '#ff5f56',
  termYellow: '#ffbd2e',
  termGreen: '#27c93f',
};

// ─── Section wrapper ──────────────────────────────────────────────────────────
function Section({ id, title, description, children }: {
  id: string;
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      style={{ marginBottom: 88 }}
    >
      <div style={{ marginBottom: 32 }}>
        <p style={{
          fontFamily: 'ui-monospace, monospace',
          fontSize: 11,
          fontWeight: 500,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: COLORS.mute,
          margin: '0 0 8px',
        }}>
          Component
        </p>
        <h2 style={{
          fontFamily: `'SF Pro Rounded', 'Nunito', system-ui, sans-serif`,
          fontSize: 24,
          fontWeight: 600,
          lineHeight: 1.33,
          color: COLORS.primary,
          margin: '0 0 8px',
        }}>
          {title}
        </h2>
        {description && (
          <p style={{ fontSize: 16, color: COLORS.body, lineHeight: 1.5, margin: 0, maxWidth: 560 }}>
            {description}
          </p>
        )}
      </div>
      <div style={{
        background: COLORS.canvas,
        border: `1px solid ${COLORS.hairline}`,
        borderRadius: 12,
        padding: 32,
      }}>
        {children}
      </div>
    </motion.section>
  );
}

// ─── Token pill ───────────────────────────────────────────────────────────────
function Token({ label }: { label: string }) {
  return (
    <span style={{
      background: COLORS.surfaceSoft,
      fontFamily: 'ui-monospace, monospace',
      fontSize: 12,
      padding: '3px 8px',
      borderRadius: 9999,
      color: COLORS.charcoal,
    }}>
      {label}
    </span>
  );
}

// ─── Terminal card (from design.md component.terminal-card) ──────────────────
function TerminalCard({ lines }: { lines: string[] }) {
  return (
    <div style={{
      background: COLORS.surfaceSoft,
      border: `1px solid ${COLORS.hairline}`,
      borderRadius: 12,
      padding: 16,
      fontFamily: 'ui-monospace, monospace',
      fontSize: 13,
    }}>
      {/* Traffic lights */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {[COLORS.termRed, COLORS.termYellow, COLORS.termGreen].map((c) => (
          <span key={c} style={{ width: 12, height: 12, borderRadius: '50%', background: c, display: 'inline-block' }} />
        ))}
      </div>
      {lines.map((l, i) => (
        <div key={i} style={{ color: l.startsWith('#') ? COLORS.mute : COLORS.primary, lineHeight: 1.9 }}>
          {l}
        </div>
      ))}
    </div>
  );
}

// ─── Row helper ───────────────────────────────────────────────────────────────
function Row({ children, gap = 12, wrap = true }: { children: React.ReactNode; gap?: number; wrap?: boolean }) {
  return (
    <div style={{ display: 'flex', flexWrap: wrap ? 'wrap' : 'nowrap', gap, alignItems: 'center' }}>
      {children}
    </div>
  );
}

// ─── Mock data ────────────────────────────────────────────────────────────────
const RETURNS = [
  { id: 'RET-9841', product: 'Nike Air Max 270', cause: 'Size/Fit', confidence: 94, status: 'Approved' },
  { id: 'RET-9840', product: 'Samsung Galaxy Tab S9', cause: 'Quality Defect', confidence: 88, status: 'Escalated' },
  { id: 'RET-9839', product: "Levi's 501 Jeans", cause: 'Wrong Item', confidence: 97, status: 'Approved' },
  { id: 'RET-9838', product: 'Dyson V15 Vacuum', cause: 'Damaged Transit', confidence: 79, status: 'Reviewing' },
  { id: 'RET-9837', product: 'Apple AirPods Pro 2', cause: 'Changed Mind', confidence: 91, status: 'Rejected' },
];

const AGENTS = ['Intake Agent', 'Root Cause Agent', 'Retrieval Agent', 'Decision Agent'];

// ─── Main Showcase ────────────────────────────────────────────────────────────
export default function DesignShowcase() {
  const [sliderVal, setSliderVal] = useState([68]);
  const [progress] = useState(73);
  const [toggleAlign, setToggleAlign] = useState('left');

  return (
    <div style={{ background: COLORS.canvas, minHeight: '100vh' }}>
      {/* ── Sticky nav ── */}
      <nav style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: COLORS.canvas,
        borderBottom: `1px solid ${COLORS.hairline}`,
        height: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 clamp(20px, 5vw, 80px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            width: 22, height: 22, borderRadius: 4,
            background: COLORS.primary, display: 'inline-block',
          }} />
          <span style={{ fontSize: 14, fontWeight: 500, letterSpacing: '-0.01em' }}>
            ReturnIQ · Design System
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* design.md: search-pill */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: COLORS.surfaceSoft,
            borderRadius: 9999, padding: '8px 16px', height: 36,
          }}>
            <Search size={13} color={COLORS.mute} />
            <span style={{ fontSize: 14, color: COLORS.mute }}>Search components…</span>
          </div>
          <Button variant="outline" size="sm" style={{ borderRadius: 9999 }}>
            Sign in
          </Button>
          {/* design.md: button-primary */}
          <Button size="sm" style={{ borderRadius: 9999, background: COLORS.primary }}>
            Download
          </Button>
        </div>
      </nav>

      {/* ── Breadcrumb bar ── */}
      <div style={{
        padding: '12px clamp(20px, 5vw, 80px)',
        borderBottom: `1px solid ${COLORS.hairline}`,
      }}>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="#" style={{ fontSize: 12 }}>ReturnIQ</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator><ChevronRight size={12} /></BreadcrumbSeparator>
            <BreadcrumbItem>
              <BreadcrumbLink href="#" style={{ fontSize: 12 }}>Frontend</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator><ChevronRight size={12} /></BreadcrumbSeparator>
            <BreadcrumbItem>
              <BreadcrumbPage style={{ fontSize: 12 }}>Design System Showcase</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      {/* ── Hero ── */}
      <div style={{
        textAlign: 'center',
        maxWidth: 720,
        margin: '0 auto',
        padding: '88px clamp(20px, 5vw, 80px) 64px',
      }}>
        {/* design.md: install-snippet */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 12,
          background: COLORS.surfaceSoft,
          borderRadius: 9999, padding: '12px 20px', height: 48,
          fontFamily: 'ui-monospace, monospace', fontSize: 15,
          marginBottom: 32,
        }}>
          <Terminal size={14} color={COLORS.mute} />
          <span>shadcn · mira · radix-ui · tailwind</span>
          <ChevronRight size={13} color={COLORS.mute} />
        </div>

        {/* design.md: typography.display-xl */}
        <h1 style={{
          fontFamily: `'SF Pro Rounded', 'Nunito', system-ui, sans-serif`,
          fontSize: 'clamp(28px, 5vw, 36px)',
          fontWeight: 500,
          lineHeight: 1.11,
          color: COLORS.primary,
          margin: '0 0 20px',
        }}>
          ReturnIQ Component Showcase
        </h1>
        <p style={{ fontSize: 16, color: COLORS.body, lineHeight: 1.5, marginBottom: 32 }}>
          Every shadcn/ui Mira component exercised with real ReturnIQ domain content —
          returns, agents, root causes, and decisions.
        </p>
        <Row gap={10} wrap={false} children={
          <>
            <Button style={{ borderRadius: 9999, background: COLORS.primary, margin: '0 auto' }}>
              Browse Components ↓
            </Button>
          </>
        } />
      </div>

      {/* ── Content column ── */}
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '0 clamp(20px, 5vw, 80px) 88px' }}>

        {/* ── 1. Buttons ── */}
        <Section id="buttons" title="Buttons" description="Primary actions follow design.md — pill geometry (rounded-full), pure black fills, no gradients.">
          <Row gap={10}>
            <Button style={{ borderRadius: 9999, background: COLORS.primary }}>Approve Return</Button>
            <Button variant="outline" style={{ borderRadius: 9999, border: `1px solid ${COLORS.hairlineStrong}` }}>Escalate</Button>
            <Button variant="ghost" style={{ borderRadius: 9999 }}>View Details</Button>
            <Button variant="destructive" style={{ borderRadius: 9999 }}>Reject</Button>
            <Button disabled style={{ borderRadius: 9999 }}>Processing…</Button>
          </Row>
          <Separator style={{ margin: '24px 0' }} />
          <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>Sizes</p>
          <Row gap={8}>
            {(['xs', 'sm', 'default', 'lg'] as const).map((s) => (
              <Button key={s} size={s} style={{ borderRadius: 9999, background: COLORS.primary }}>
                {s === 'default' ? 'md' : s}
              </Button>
            ))}
          </Row>
          <Separator style={{ margin: '24px 0' }} />
          <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>Icon buttons</p>
          <Row gap={8}>
            <Button size="icon" style={{ borderRadius: 9999, background: COLORS.primary }}><Brain size={14} /></Button>
            <Button size="icon-sm" variant="outline" style={{ borderRadius: 9999 }}><RefreshCw size={13} /></Button>
            <Button size="icon-lg" variant="ghost" style={{ borderRadius: 9999 }}><Settings size={15} /></Button>
          </Row>
          <Separator style={{ margin: '24px 0' }} />
          {/* design.md: button-pill-on-dark */}
          <div style={{ background: COLORS.surfaceDark, borderRadius: 12, padding: 24, display: 'inline-flex', flexDirection: 'column', gap: 12 }}>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, margin: 0 }}>Max Plan · Dark surface CTA</p>
            <Button style={{ borderRadius: 9999, background: COLORS.canvas, color: COLORS.primary, width: 'fit-content' }}>
              Get Max
            </Button>
          </div>
        </Section>

        {/* ── 2. Badges ── */}
        <Section id="badges" title="Badges" description="Compact status indicators for return states, agent health, and confidence tiers.">
          <Row gap={8}>
            <Badge>Approved</Badge>
            <Badge variant="secondary">Reviewing</Badge>
            <Badge variant="outline">Escalated</Badge>
            <Badge variant="destructive">Rejected</Badge>
            <Badge variant="ghost">Pending</Badge>
          </Row>
          <Separator style={{ margin: '20px 0' }} />
          <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>With icons</p>
          <Row gap={8}>
            <Badge><CheckCircle2 size={10} /> Auto-Approved</Badge>
            <Badge variant="destructive"><AlertTriangle size={10} /> Anomaly</Badge>
            <Badge variant="secondary"><Brain size={10} /> AI Confidence 87%</Badge>
            <Badge variant="outline"><Cpu size={10} /> Agent Healthy</Badge>
          </Row>
        </Section>

        {/* ── 3. Cards ── */}
        <Section id="cards" title="Cards" description="Hairline-bordered surfaces (rounded-lg, 1px) used for return summaries, agent stats, and AI insights.">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
            <Card>
              <CardHeader>
                <CardTitle>RET-9841</CardTitle>
                <CardDescription>Nike Air Max 270 — Size 10</CardDescription>
                <CardAction><Badge>Approved</Badge></CardAction>
              </CardHeader>
              <CardContent>
                <p style={{ color: COLORS.body, fontSize: 13, lineHeight: 1.5, margin: 0 }}>
                  Root cause: <strong>Size/Fit issue</strong>. AI confidence 94%. Auto-approved in 1m 12s.
                </p>
              </CardContent>
              <CardFooter>
                <Button size="sm" style={{ borderRadius: 9999, background: COLORS.primary }}>View Case</Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Root Cause Agent</CardTitle>
                <CardDescription>A2 · Model v2.3-fine</CardDescription>
                <CardAction><Badge variant="outline"><Cpu size={10} /> Healthy</Badge></CardAction>
              </CardHeader>
              <CardContent>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {[['Latency', '820ms'], ['Error Rate', '0.4%'], ['Uptime', '99.7%'], ['Queue', '12']].map(([k, v]) => (
                    <div key={k}>
                      <p style={{ fontSize: 10, color: COLORS.mute, margin: '0 0 2px', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{k}</p>
                      <p style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{v}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* design.md: pricing-card-dark */}
            <Card style={{ background: COLORS.surfaceDark, color: '#fff', border: 'none' }}>
              <CardHeader>
                <CardTitle style={{ color: '#fff' }}>Anomaly Cluster</CardTitle>
                <CardDescription style={{ color: 'rgba(255,255,255,0.6)' }}>Batch NKE-270 · High risk</CardDescription>
                <CardAction><Badge variant="destructive"><ShieldAlert size={10} /> 48 flags</Badge></CardAction>
              </CardHeader>
              <CardContent>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, lineHeight: 1.5, margin: 0 }}>
                  Supplier batch variance detected in mould sizing for athletic footwear SKUs. Recommend supplier QA review.
                </p>
              </CardContent>
              <CardFooter>
                <Button style={{ borderRadius: 9999, background: COLORS.canvas, color: COLORS.primary }}>
                  Review Now
                </Button>
              </CardFooter>
            </Card>
          </div>
        </Section>

        {/* ── 4. Alerts ── */}
        <Section id="alerts" title="Alerts" description="Contextual system messages — anomaly detections, agent degradations, and process confirmations.">
          <div style={{ display: 'grid', gap: 12 }}>
            <Alert>
              <Info size={14} />
              <AlertTitle>Sync Complete</AlertTitle>
              <AlertDescription>All 4 agents are live. Last sync 20 seconds ago.</AlertDescription>
            </Alert>
            <Alert variant="destructive">
              <AlertTriangle size={14} />
              <AlertTitle>Retrieval Agent Degraded</AlertTitle>
              <AlertDescription>Latency at 1.24s (threshold: 1.0s). Error rate 1.8%. Monitoring escalation.</AlertDescription>
            </Alert>
          </div>
        </Section>

        {/* ── 5. Tabs ── */}
        <Section id="tabs" title="Tabs" description="Navigation between return queue views, agent panels, and analytics sections.">
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview"><LayoutDashboard size={12} /> Overview</TabsTrigger>
              <TabsTrigger value="queue"><Package size={12} /> Queue</TabsTrigger>
              <TabsTrigger value="agents"><Cpu size={12} /> Agents</TabsTrigger>
              <TabsTrigger value="settings"><Settings size={12} /> Settings</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" style={{ paddingTop: 20 }}>
              <p style={{ color: COLORS.body, fontSize: 14, lineHeight: 1.5 }}>
                <strong>Overview:</strong> 1,442 returns today · 73.2% auto-approved · avg resolution 2m 18s · AI confidence 87.4%.
              </p>
            </TabsContent>
            <TabsContent value="queue" style={{ paddingTop: 20 }}>
              <p style={{ color: COLORS.body, fontSize: 14, lineHeight: 1.5 }}>
                <strong>Queue:</strong> 48 returns pending · 6 escalated · 12 flagged for manual review.
              </p>
            </TabsContent>
            <TabsContent value="agents" style={{ paddingTop: 20 }}>
              <p style={{ color: COLORS.body, fontSize: 14, lineHeight: 1.5 }}>
                <strong>Agents:</strong> A1 Healthy · A2 Healthy · A3 Degraded · A4 Healthy.
              </p>
            </TabsContent>
            <TabsContent value="settings" style={{ paddingTop: 20 }}>
              <p style={{ color: COLORS.body, fontSize: 14, lineHeight: 1.5 }}>
                <strong>Settings:</strong> Configure auto-approval thresholds, confidence cutoffs, and agent timeouts.
              </p>
            </TabsContent>
          </Tabs>
          <Separator style={{ margin: '24px 0' }} />
          <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>Line variant</p>
          <Tabs defaultValue="a">
            <TabsList variant="line">
              <TabsTrigger value="a">7-Day</TabsTrigger>
              <TabsTrigger value="b">30-Day</TabsTrigger>
              <TabsTrigger value="c">90-Day</TabsTrigger>
            </TabsList>
          </Tabs>
        </Section>

        {/* ── 6. Table ── */}
        <Section id="table" title="Table" description="The primary data surface for the returns queue and evidence feed.">
          <Table>
            <TableCaption>Recent returns processed by the AI pipeline</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>Return ID</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Root Cause</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {RETURNS.map((r) => (
                <TableRow key={r.id}>
                  <TableCell style={{ fontFamily: 'ui-monospace', fontSize: 12, color: '#3469d8' }}>{r.id}</TableCell>
                  <TableCell style={{ fontWeight: 500 }}>{r.product}</TableCell>
                  <TableCell style={{ color: COLORS.body }}>{r.cause}</TableCell>
                  <TableCell>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 48, height: 4, background: '#e9edf2', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ width: `${r.confidence}%`, height: '100%', background: r.confidence > 90 ? '#2d8060' : r.confidence > 80 ? '#3469d8' : '#bd7b20', borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11, fontFamily: 'ui-monospace', color: COLORS.mute }}>{r.confidence}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={r.status === 'Approved' ? 'default' : r.status === 'Rejected' ? 'destructive' : 'outline'}
                      style={{ borderRadius: 9999 }}
                    >
                      {r.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Section>

        {/* ── 7. Form Controls ── */}
        <Section id="forms" title="Form Controls" description="Inputs, selects, checkboxes, radio groups, switches — styled for the return intake form.">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div style={{ display: 'grid', gap: 6 }}>
              <Label htmlFor="product-id">Product ID</Label>
              <Input id="product-id" placeholder="e.g. NKE-270-BLK-10" style={{ borderRadius: 9999 }} />
            </div>
            <div style={{ display: 'grid', gap: 6 }}>
              <Label htmlFor="agent-select">Assign Agent</Label>
              <Select>
                <SelectTrigger id="agent-select" style={{ borderRadius: 9999 }}>
                  <SelectValue placeholder="Select agent…" />
                </SelectTrigger>
                <SelectContent>
                  {AGENTS.map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div style={{ display: 'grid', gap: 6, gridColumn: '1 / -1' }}>
              <Label htmlFor="reason">Return Reason</Label>
              <Textarea id="reason" placeholder="Describe the return reason in detail…" style={{ borderRadius: 12, minHeight: 90 }} />
            </div>
          </div>
          <Separator style={{ margin: '24px 0' }} />
          <div style={{ display: 'grid', gap: 14 }}>
            <p style={{ fontSize: 13, color: COLORS.mute, margin: 0 }}>Checkboxes</p>
            {['Auto-approve if confidence ≥ 90%', 'Notify customer on resolution', 'Flag for supplier QA review'].map((label) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Checkbox id={label} />
                <Label htmlFor={label} style={{ fontSize: 14, cursor: 'pointer' }}>{label}</Label>
              </div>
            ))}
          </div>
          <Separator style={{ margin: '24px 0' }} />
          <div style={{ display: 'grid', gap: 14 }}>
            <p style={{ fontSize: 13, color: COLORS.mute, margin: 0 }}>Radio Group — Return Category</p>
            <RadioGroup defaultValue="size">
              {[['size', 'Size / Fit Issue'], ['defect', 'Quality Defect'], ['wrong', 'Wrong Item Sent'], ['mind', 'Changed Mind']].map(([v, l]) => (
                <div key={v} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <RadioGroupItem value={v} id={`radio-${v}`} />
                  <Label htmlFor={`radio-${v}`} style={{ cursor: 'pointer' }}>{l}</Label>
                </div>
              ))}
            </RadioGroup>
          </div>
          <Separator style={{ margin: '24px 0' }} />
          <div style={{ display: 'grid', gap: 14 }}>
            <p style={{ fontSize: 13, color: COLORS.mute, margin: 0 }}>Switches</p>
            {[
              ['Auto-approve enabled', true],
              ['Email notifications', false],
              ['Anomaly alerting', true],
            ].map(([label, def]) => (
              <div key={String(label)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: 320 }}>
                <Label style={{ fontSize: 14 }}>{label as string}</Label>
                <Switch defaultChecked={def as boolean} />
              </div>
            ))}
          </div>
        </Section>

        {/* ── 8. Slider & Progress ── */}
        <Section id="slider-progress" title="Slider & Progress" description="Confidence thresholds, auto-approval rates, and agent throughput visualised.">
          <div style={{ display: 'grid', gap: 24, maxWidth: 480 }}>
            <div style={{ display: 'grid', gap: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Label>Auto-Approve Confidence Threshold</Label>
                <span style={{ fontSize: 13, fontFamily: 'ui-monospace', color: COLORS.mute }}>{sliderVal[0]}%</span>
              </div>
              <Slider value={sliderVal} onValueChange={setSliderVal} min={50} max={100} step={1} />
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Label>Auto-Approved Rate</Label>
                <span style={{ fontSize: 13, fontFamily: 'ui-monospace', color: COLORS.mute }}>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              <Label>Retrieval Agent Uptime</Label>
              <Progress value={97} />
            </div>
          </div>
        </Section>

        {/* ── 9. Skeleton & Spinner ── */}
        <Section id="loading" title="Skeleton & Spinner" description="Loading states for async agent responses and return data fetching.">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
            <div style={{ display: 'grid', gap: 10 }}>
              <p style={{ fontSize: 13, color: COLORS.mute, margin: 0 }}>Skeleton</p>
              <Skeleton style={{ height: 16, width: '60%', borderRadius: 9999 }} />
              <Skeleton style={{ height: 16, width: '80%', borderRadius: 9999 }} />
              <Skeleton style={{ height: 16, width: '45%', borderRadius: 9999 }} />
              <Skeleton style={{ height: 80, width: '100%', borderRadius: 12 }} />
            </div>
            <div style={{ display: 'grid', gap: 16 }}>
              <p style={{ fontSize: 13, color: COLORS.mute, margin: 0 }}>Spinner</p>
              <Row gap={16}>
                {(['xs', 'sm', 'md', 'lg'] as const).map((s) => (
                  <div key={s} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                    <Spinner className={s === 'xs' ? 'w-3 h-3' : s === 'sm' ? 'w-4 h-4' : s === 'md' ? 'w-5 h-5' : 'w-6 h-6'} />
                    <span style={{ fontSize: 10, color: COLORS.mute, fontFamily: 'ui-monospace' }}>{s}</span>
                  </div>
                ))}
              </Row>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Spinner />
                <span style={{ fontSize: 13, color: COLORS.body }}>Running root cause inference…</span>
              </div>
            </div>
          </div>
        </Section>

        {/* ── 10. Accordion ── */}
        <Section id="accordion" title="Accordion" description="FAQ-style collapse panels — design.md faq-row pattern for policy questions.">
          <Accordion type="single" collapsible style={{ maxWidth: 640 }}>
            {[
              {
                q: 'How does the Root Cause Agent determine attribution?',
                a: 'The Root Cause Agent uses a fine-tuned LLM (GPT-4o, v2.3) trained on 2M historical return records. It clusters semantic signals from customer notes, product metadata, and supplier batch data to output a root cause with a confidence score.',
              },
              {
                q: 'When is a return automatically approved?',
                a: 'Returns are auto-approved when the AI confidence score exceeds the configured threshold (default: 90%). The Decision Agent applies policy rules on top of the confidence score, including SKU-specific overrides and supplier flags.',
              },
              {
                q: 'What happens when the Retrieval Agent is degraded?',
                a: 'The system falls back to a cached policy snapshot (max 24h stale). A degradation alert is surfaced on the Agent Health Monitor and the on-call team is paged via the configured webhook.',
              },
              {
                q: 'Can I customise the auto-approval confidence threshold?',
                a: 'Yes — navigate to Settings → Agent Configuration → Decision Agent and adjust the confidence threshold slider. Changes take effect on the next return processed.',
              },
            ].map((item, i) => (
              <AccordionItem key={i} value={`item-${i}`} style={{ borderBottom: `1px solid ${COLORS.hairline}` }}>
                <AccordionTrigger style={{ fontSize: 15, fontWeight: 500, padding: '16px 0' }}>
                  {item.q}
                </AccordionTrigger>
                <AccordionContent style={{ color: COLORS.body, lineHeight: 1.6, paddingBottom: 16 }}>
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Section>

        {/* ── 11. Dialog & Sheet ── */}
        <Section id="overlays" title="Dialog, Sheet & Alert Dialog" description="Overlay surfaces for return escalation, settings panels, and destructive confirmations.">
          <Row gap={12}>
            {/* Dialog */}
            <Dialog>
              <DialogTrigger asChild>
                <Button style={{ borderRadius: 9999, background: COLORS.primary }}>Open Dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Escalate RET-9840</DialogTitle>
                  <DialogDescription>
                    This return will be routed to a human agent. Provide additional context below.
                  </DialogDescription>
                </DialogHeader>
                <div style={{ display: 'grid', gap: 8, padding: '8px 0' }}>
                  <Label htmlFor="escalate-reason">Reason for escalation</Label>
                  <Textarea id="escalate-reason" placeholder="Describe why this needs human review…" style={{ borderRadius: 8, minHeight: 80 }} />
                </div>
                <DialogFooter>
                  <Button variant="outline" style={{ borderRadius: 9999 }}>Cancel</Button>
                  <Button style={{ borderRadius: 9999, background: COLORS.primary }}>Escalate</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Sheet */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" style={{ borderRadius: 9999 }}>
                  <PanelLeft size={13} /> Agent Settings
                </Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Agent Configuration</SheetTitle>
                  <SheetDescription>Adjust thresholds, timeouts, and fallback policies.</SheetDescription>
                </SheetHeader>
                <div style={{ padding: '24px 0', display: 'grid', gap: 20 }}>
                  {AGENTS.map((a, i) => (
                    <div key={a} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div>
                        <p style={{ fontSize: 13, fontWeight: 500, margin: '0 0 2px' }}>{a}</p>
                        <p style={{ fontSize: 11, color: COLORS.mute, margin: 0, fontFamily: 'ui-monospace' }}>A{i + 1}</p>
                      </div>
                      <Switch defaultChecked={a !== 'Retrieval Agent'} />
                    </div>
                  ))}
                </div>
              </SheetContent>
            </Sheet>

            {/* Alert Dialog */}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" style={{ borderRadius: 9999 }}>
                  <Trash2 size={13} /> Purge Queue
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Purge Return Queue?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete all 48 pending returns from the queue. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel style={{ borderRadius: 9999 }}>Cancel</AlertDialogCancel>
                  <AlertDialogAction style={{ borderRadius: 9999, background: '#bd4e44', border: 'none' }}>
                    Yes, purge
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </Row>
        </Section>

        {/* ── 12. Dropdown & Popover ── */}
        <Section id="menus" title="Dropdown, Popover & Tooltip" description="Contextual menus and on-demand overlays for return row actions and agent quick-info.">
          <Row gap={16}>
            {/* Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" style={{ borderRadius: 9999 }}>
                  <MoreHorizontal size={14} /> Actions
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" style={{ minWidth: 200 }}>
                <DropdownMenuLabel>Return RET-9841</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem><CheckCircle2 size={13} /> Approve</DropdownMenuItem>
                <DropdownMenuItem><AlertTriangle size={13} /> Escalate</DropdownMenuItem>
                <DropdownMenuItem><FileSearch size={13} /> View Evidence</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem style={{ color: '#bd4e44' }}><Trash2 size={13} /> Reject &amp; Archive</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" style={{ borderRadius: 9999 }}>
                  <Brain size={13} /> AI Insight
                </Button>
              </PopoverTrigger>
              <PopoverContent style={{ width: 320, fontSize: 13, lineHeight: 1.6 }}>
                <p style={{ fontWeight: 600, margin: '0 0 8px' }}>Sizing Anomaly Cluster</p>
                <p style={{ color: COLORS.body, margin: '0 0 12px' }}>
                  Batch NKE-270-BLK shows +34% size returns vs baseline. Root cause: supplier mould variance. Confidence: 87%.
                </p>
                <Button size="sm" style={{ borderRadius: 9999, background: COLORS.primary, width: '100%' }}>
                  Review Full Report
                </Button>
              </PopoverContent>
            </Popover>

            {/* Tooltip */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="icon" variant="ghost" style={{ borderRadius: 9999 }}>
                  <Info size={15} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>AI confidence ≥ 90% triggers auto-approval</p>
              </TooltipContent>
            </Tooltip>

            {/* HoverCard */}
            <HoverCard>
              <HoverCardTrigger asChild>
                <Button variant="link" style={{ fontFamily: 'ui-monospace' }}>@root-cause-agent</Button>
              </HoverCardTrigger>
              <HoverCardContent style={{ width: 280 }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{ width: 36, height: 36, borderRadius: 9999, background: '#edf3ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Brain size={16} color="#3469d8" />
                  </div>
                  <div>
                    <p style={{ fontWeight: 600, margin: '0 0 2px', fontSize: 13 }}>Root Cause Agent</p>
                    <p style={{ color: COLORS.mute, fontSize: 11, fontFamily: 'ui-monospace', margin: '0 0 8px' }}>A2 · v2.3-fine · GPT-4o</p>
                    <p style={{ color: COLORS.body, fontSize: 12, lineHeight: 1.5, margin: 0 }}>
                      Classifies return root causes using fine-tuned LLM with supplier batch data.
                    </p>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>
          </Row>
        </Section>

        {/* ── 13. Command ── */}
        <Section id="command" title="Command Palette" description="Quick navigation and return search — design.md search-pill evolved into a full command surface.">
          <div style={{ maxWidth: 480, border: `1px solid ${COLORS.hairline}`, borderRadius: 8, overflow: 'hidden' }}>
            <Command>
              <CommandInput placeholder="Search returns, agents, SKUs…" />
              <CommandList>
                <CommandEmpty>No results found.</CommandEmpty>
                <CommandGroup heading="Recent Returns">
                  {RETURNS.slice(0, 3).map((r) => (
                    <CommandItem key={r.id}>
                      <Package size={13} />
                      <span>{r.id}</span>
                      <span style={{ color: COLORS.mute, fontSize: 11, marginLeft: 'auto' }}>{r.product}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
                <CommandSeparator />
                <CommandGroup heading="Agents">
                  {[
                    { name: 'Intake Agent', icon: FileSearch },
                    { name: 'Root Cause Agent', icon: Brain },
                    { name: 'Decision Agent', icon: Zap },
                  ].map(({ name, icon: Icon }) => (
                    <CommandItem key={name}>
                      <Icon size={13} />
                      {name}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </div>
        </Section>

        {/* ── 14. Toggle & ToggleGroup ── */}
        <Section id="toggles" title="Toggle & Toggle Group" description="View mode switchers and text editor controls within the return intake form.">
          <div style={{ display: 'grid', gap: 20 }}>
            <div>
              <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 10 }}>Single Toggle</p>
              <Row gap={8}>
                <Toggle aria-label="Bold"><Bold size={13} /></Toggle>
                <Toggle aria-label="Italic"><Italic size={13} /></Toggle>
                <Toggle aria-label="Underline"><Underline size={13} /></Toggle>
              </Row>
            </div>
            <div>
              <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 10 }}>Toggle Group — View Mode</p>
              <ToggleGroup
                type="single"
                value={toggleAlign}
                onValueChange={(v) => v && setToggleAlign(v)}
              >
                <ToggleGroupItem value="left" aria-label="List view">
                  <List size={13} />
                </ToggleGroupItem>
                <ToggleGroupItem value="center" aria-label="Grid view">
                  <Grid3x3 size={13} />
                </ToggleGroupItem>
                <ToggleGroupItem value="right" aria-label="Detail view">
                  <AlignLeft size={13} />
                </ToggleGroupItem>
              </ToggleGroup>
            </div>
          </div>
        </Section>

        {/* ── 15. Collapsible ── */}
        <Section id="collapsible" title="Collapsible" description="Expandable agent trace logs and evidence panels.">
          <div style={{ maxWidth: 560 }}>
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="outline" style={{ borderRadius: 9999, width: '100%', justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Terminal size={13} /> Agent Trace — RET-9841
                  </span>
                  <ChevronDown size={13} />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <TerminalCard lines={[
                  '# ReturnIQ Agent Pipeline · RET-9841',
                  '[A1] Intake: product=NKE-270-BLK-10 customer=Aiden Walsh',
                  '[A2] Root cause inference → size_fit (conf=0.94)',
                  '[A3] Policy retrieval → auto_approve_eligible=true',
                  '[A4] Decision: APPROVE · elapsed=1m12s',
                ]} />
              </CollapsibleContent>
            </Collapsible>
          </div>
        </Section>

        {/* ── 16. Scroll Area ── */}
        <Section id="scroll-area" title="Scroll Area" description="Constrained-height lists for long return queues and agent logs.">
          <ScrollArea style={{ height: 200, border: `1px solid ${COLORS.hairline}`, borderRadius: 8 }}>
            <div style={{ padding: 16 }}>
              {Array.from({ length: 20 }, (_, i) => ({
                id: `RET-${9841 - i}`,
                product: RETURNS[i % RETURNS.length].product,
                status: RETURNS[i % RETURNS.length].status,
              })).map((r) => (
                <div key={r.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 0', borderBottom: `1px solid ${COLORS.hairline}`,
                  fontSize: 13,
                }}>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 12, color: '#3469d8' }}>{r.id}</span>
                  <span style={{ color: COLORS.body }}>{r.product}</span>
                  <Badge variant={r.status === 'Approved' ? 'default' : 'outline'} style={{ borderRadius: 9999 }}>
                    {r.status}
                  </Badge>
                </div>
              ))}
            </div>
          </ScrollArea>
        </Section>

        {/* ── 17. Avatar & Bubble ── */}
        <Section id="avatar-bubble" title="Avatar & Bubble" description="User avatars for the agent team view, and chat bubbles for AI conversation interfaces.">
          <div style={{ display: 'grid', gap: 24 }}>
            <div>
              <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>Avatars</p>
              <Row gap={8}>
                {[
                  { initials: 'LK', color: '#3469d8' },
                  { initials: 'A1', color: '#2d8060' },
                  { initials: 'A2', color: '#7c3aed' },
                  { initials: 'A3', color: '#bd7b20' },
                  { initials: 'A4', color: '#bd4e44' },
                ].map(({ initials, color }) => (
                  <Tooltip key={initials}>
                    <TooltipTrigger>
                      <div style={{
                        width: 36, height: 36, borderRadius: 9999,
                        background: color, color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        font: '500 12px var(--font-display)',
                      }}>
                        {initials}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>{initials === 'LK' ? 'Lesha K (Admin)' : `Agent ${initials}`}</TooltipContent>
                  </Tooltip>
                ))}
              </Row>
            </div>
            <div>
              <p style={{ fontSize: 13, color: COLORS.mute, marginBottom: 12 }}>Bubbles (AI conversation)</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 420 }}>
                <div style={{ display: 'flex', gap: 10 }}>
                  <div style={{ width: 28, height: 28, borderRadius: 9999, background: '#edf3ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={13} color="#3469d8" />
                  </div>
                  <Bubble style={{ background: COLORS.surfaceSoft, border: `1px solid ${COLORS.hairline}`, borderRadius: 12, padding: '10px 14px', fontSize: 13 }}>
                    Why was RET-9841 auto-approved?
                  </Bubble>
                </div>
                <div style={{ display: 'flex', gap: 10, flexDirection: 'row-reverse' }}>
                  <div style={{ width: 28, height: 28, borderRadius: 9999, background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Brain size={13} color="#fff" />
                  </div>
                  <Bubble style={{ background: COLORS.primary, color: '#fff', borderRadius: 12, padding: '10px 14px', fontSize: 13 }}>
                    Confidence score was 94% (threshold: 90%). Root cause: size/fit — highest-confidence category. Policy check passed.
                  </Bubble>
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* ── 18. Kbd ── */}
        <Section id="kbd" title="Keyboard Shortcut" description="Command palette and accessibility keyboard hint labels.">
          <div style={{ display: 'grid', gap: 12 }}>
            {[
              ['Open command palette', ['⌘', 'K']],
              ['Approve selected return', ['⌘', 'Enter']],
              ['Escalate return', ['⌘', 'Shift', 'E']],
              ['Refresh agent status', ['R']],
            ].map(([action, keys]) => (
              <div key={action as string} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: 400 }}>
                <span style={{ fontSize: 13, color: COLORS.body }}>{action as string}</span>
                <Row gap={4}>
                  {(keys as string[]).map((k) => <Kbd key={k}>{k}</Kbd>)}
                </Row>
              </div>
            ))}
          </div>
        </Section>

        {/* ── 19. Empty state ── */}
        <Section id="empty" title="Empty State" description="Zero-data views for an empty return queue or no search results.">
          <Empty>
            <EmptyMedia variant="icon">
              <Package size={20} color={COLORS.mute} />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle>No returns in queue</EmptyTitle>
              <EmptyDescription>All returns have been processed. New submissions will appear here automatically.</EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button style={{ borderRadius: 9999, background: COLORS.primary }}>
                <RefreshCw size={13} /> Refresh Queue
              </Button>
            </EmptyContent>
          </Empty>
        </Section>

        {/* ── 20. Pagination ── */}
        <Section id="pagination" title="Pagination" description="Navigate through large return queues and historical reports.">
          <Pagination>
            <PaginationContent>
              <PaginationItem><PaginationPrevious href="#" /></PaginationItem>
              <PaginationItem><PaginationLink href="#">1</PaginationLink></PaginationItem>
              <PaginationItem><PaginationLink href="#" isActive>2</PaginationLink></PaginationItem>
              <PaginationItem><PaginationLink href="#">3</PaginationLink></PaginationItem>
              <PaginationItem><PaginationEllipsis /></PaginationItem>
              <PaginationItem><PaginationLink href="#">12</PaginationLink></PaginationItem>
              <PaginationItem><PaginationNext href="#" /></PaginationItem>
            </PaginationContent>
          </Pagination>
        </Section>

        {/* ── 21. Terminal card (design.md) ── */}
        <Section id="terminal" title="Terminal Card" description="Product preview surface from design.md — macOS traffic lights + monospace code output.">
          <div style={{ maxWidth: 560 }}>
            <TerminalCard lines={[
              '# ReturnIQ Agent Pipeline',
              '$ returniq start --agents all',
              '',
              '# Starting 4 agents...',
              '[A1] Intake Agent         → healthy (340ms)',
              '[A2] Root Cause Agent     → healthy (820ms)',
              '[A3] Retrieval Agent      → degraded (1.24s) ⚠',
              '[A4] Decision Agent       → healthy (210ms)',
              '',
              '# Processing RET-9841...',
              '[A2] root_cause=size_fit conf=0.94',
              '[A4] decision=APPROVE elapsed=1m12s',
            ]} />
          </div>
          <div style={{ marginTop: 16 }}>
            {/* design.md: command-tag */}
            <Row gap={8}>
              <Token label="returniq start" />
              <Token label="returniq status" />
              <Token label="returniq replay RET-9841" />
            </Row>
          </div>
        </Section>

        {/* ── 22. CTA strip dark ── */}
        <section style={{
          background: COLORS.surfaceDark,
          borderRadius: 12,
          padding: '32px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 20,
          marginBottom: 88,
        }}>
          <div>
            <p style={{ fontSize: 11, fontFamily: 'ui-monospace', letterSpacing: '0.08em', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', margin: '0 0 8px' }}>
              Get Started
            </p>
            <h2 style={{
              fontFamily: `'SF Pro Rounded', 'Nunito', system-ui, sans-serif`,
              fontSize: 24, fontWeight: 600, color: '#fff', margin: '0 0 8px',
            }}>
              Start automating your returns today.
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 15, margin: 0 }}>
              Deploy all 4 agents in under 5 minutes. Your data stays yours.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Button style={{ borderRadius: 9999, background: COLORS.canvas, color: COLORS.primary }}>
              <Lock size={13} /> Get Max
            </Button>
            <Button style={{ borderRadius: 9999, background: 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}>
              Read Docs
            </Button>
          </div>
        </section>

        {/* ── Footer ── */}
        <footer style={{
          borderTop: `1px solid ${COLORS.hairline}`,
          paddingTop: 32,
          paddingBottom: 32,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}>
          <p style={{ fontSize: 12, color: COLORS.mute, margin: 0 }}>
            © 2026 ReturnIQ · shadcn/ui Mira · Radix UI
          </p>
          <Row gap={20}>
            {['Dashboard', 'Docs', 'GitHub', 'Privacy', 'Terms'].map((l) => (
              <a key={l} href="#" style={{ fontSize: 12, color: COLORS.body, textDecoration: 'none' }}>
                {l}
              </a>
            ))}
          </Row>
        </footer>
      </div>
    </div>
  );
}
