import React, { useState, useEffect, useRef, ChangeEvent } from 'react';
import ResultPage from './ResultPage';
import { processReturn, uploadBulk } from '../../lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Spinner } from '@/components/ui/spinner';
import {
  ScanLine,
  ShieldOff,
  Package,
  Brain,
  BarChart2,
  SearchCode,
  BookOpen,
  Scale,
  Sparkles,
  BadgeCheck,
} from 'lucide-react';

// Live reasoning steps — no emojis, lucide icons only
const REASONING_STAGES = [
  {
    agent: 'Agent 1 — Intake',
    step: 'Scanning raw text for PII (phone, NIC, email)…',
    Icon: ScanLine,
  },
  {
    agent: 'Agent 1 — Intake',
    step: 'Redacting personal identifiers from complaint text…',
    Icon: ShieldOff,
  },
  {
    agent: 'Agent 1 — Intake',
    step: 'Extracting product, issue, and confidence score…',
    Icon: Package,
  },
  {
    agent: 'Agent 2 — Root Cause',
    step: 'Running taxonomy classifier on cleaned complaint…',
    Icon: Brain,
  },
  {
    agent: 'Agent 2 — Root Cause',
    step: 'Scoring abuse risk and top candidate labels…',
    Icon: BarChart2,
  },
  {
    agent: 'Agent 3 — Retrieval',
    step: 'Building hybrid BM25 + semantic query…',
    Icon: SearchCode,
  },
  {
    agent: 'Agent 3 — Retrieval',
    step: 'Fetching top-5 evidence snippets from corpus…',
    Icon: BookOpen,
  },
  {
    agent: 'Agent 4 — Decision',
    step: 'Applying policy rules (return window, abuse threshold)…',
    Icon: Scale,
  },
  {
    agent: 'Agent 4 — Decision',
    step: 'Synthesising final recommendation via LLM…',
    Icon: Sparkles,
  },
  {
    agent: 'Agent 4 — Decision',
    step: 'Finalising decision and generating citations…',
    Icon: BadgeCheck,
  },
];

const AGENT_COLORS: Record<string, { dot: string; label: string }> = {
  'Agent 1 — Intake': { dot: 'bg-neutral-600', label: 'text-neutral-700' },
  'Agent 2 — Root Cause': { dot: 'bg-violet-500', label: 'text-violet-700' },
  'Agent 3 — Retrieval': { dot: 'bg-amber-500', label: 'text-amber-700' },
  'Agent 4 — Decision': { dot: 'bg-emerald-500', label: 'text-emerald-700' },
};

interface RowError {
  row: number;
  field: string;
  reason: string;
}

interface SubmitReturnPageProps {
  onNavigate?: (view: string) => void;
}

export const SubmitReturnPage: React.FC<SubmitReturnPageProps> = ({
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single');

  // Single Return State
  const [singleText, setSingleText] = useState('');
  const [orderId, setOrderId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);
  const [singleOutput, setSingleOutput] = useState<unknown>(null);
  const [visibleSteps, setVisibleSteps] = useState<number[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Tick through reasoning steps while submitting
  useEffect(() => {
    if (isSubmitting) {
      let idx = 0;
      intervalRef.current = setInterval(() => {
        setVisibleSteps((prev) => [...prev, idx]);
        idx++;
        if (idx >= REASONING_STAGES.length) clearInterval(intervalRef.current!);
      }, 500);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isSubmitting]);

  // Bulk Upload State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<Record<string, unknown>[]>([]);
  const [rowErrors, setRowErrors] = useState<RowError[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const MAX_CHAR = 2000;

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleText.trim()) {
      setSingleError('Please enter the customer complaint details.');
      return;
    }
    setVisibleSteps([]);
    setIsSubmitting(true);
    setSingleError(null);

    try {
      const data = await processReturn({
        text: singleText,
        order_id: orderId || undefined,
      });
      setSingleOutput(data);
    } catch (err: unknown) {
      const error = err as Error;
      setSingleError(`Submission failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvFile(file);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      parseCsvPreview(text);
    };
    reader.readAsText(file);
  };

  const parseCsvPreview = (csvText: string) => {
    const lines = csvText.split('\n').filter((l) => l.trim().length > 0);
    if (lines.length === 0) return;

    const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
    const parsed = [];
    const errors: RowError[] = [];

    for (let i = 1; i < Math.min(lines.length, 6); i++) {
      const cols = lines[i].split(',');
      const rowData: Record<string, string> = {};
      headers.forEach((h, idx) => {
        rowData[h] = cols[idx]?.trim() || '';
      });
      parsed.push(rowData);
      if (!rowData['text'] && !rowData['complaint']) {
        errors.push({ row: i, field: 'text', reason: 'Missing return text' });
      }
    }
    setPreviewRows(parsed);
    setRowErrors(errors);
  };

  const handleBulkSubmit = async () => {
    if (!csvFile) return;
    setIsUploading(true);
    try {
      const data = await uploadBulk(csvFile);
      if (onNavigate) {
        onNavigate('bulk');
      } else {
        alert(`Bulk Job Started! Job ID: ${data.job_id || 'JOB-001'}`);
      }
    } catch (err: unknown) {
      const error = err as Error;
      alert(`Upload failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  if (singleOutput) {
    return (
      <ResultPage
        result={singleOutput}
        userRole="admin"
        onBack={() => setSingleOutput(null)}
        onNavigate={(view) => {
          if (view === 'submit') {
            setSingleOutput(null);
            setSingleText('');
            setOrderId('');
            setVisibleSteps([]);
          } else if (onNavigate) {
            onNavigate(view);
          }
        }}
      />
    );
  }

  return (
    <section className="min-h-[calc(100vh-52px)] bg-white">
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 font-sans sm:px-6 lg:px-8">
        <div className="border-b pb-4">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Submit Customer Return
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Intake Agent (Agent 1) cleans raw input, strips PII, and identifies
            affected products and issues.
          </p>
        </div>

        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="single" className="rounded-full">
              Single Return
            </TabsTrigger>
            <TabsTrigger value="bulk" className="rounded-full">
              Bulk Upload (.CSV)
            </TabsTrigger>
          </TabsList>

          {/* Single Return Tab */}
          <TabsContent value="single">
            <div className="space-y-4">
              <Card>
                <CardContent className="space-y-4 p-6">
                  <form onSubmit={handleSingleSubmit} className="space-y-4">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700">
                        Order ID / Reference (Optional)
                      </label>
                      <Input
                        placeholder="e.g. ORD-10293"
                        value={orderId}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setOrderId(e.target.value)
                        }
                        disabled={isSubmitting}
                      />
                    </div>

                    <div>
                      <div className="mb-1 flex items-center justify-between">
                        <label className="block text-sm font-medium text-gray-700">
                          Customer Complaint / Message{' '}
                          <span className="text-red-500">*</span>
                        </label>
                        <span
                          className={`text-xs ${
                            singleText.length > MAX_CHAR
                              ? 'font-bold text-red-500'
                              : 'text-gray-400'
                          }`}
                        >
                          {singleText.length} / {MAX_CHAR} characters
                        </span>
                      </div>
                      <Textarea
                        rows={5}
                        placeholder="Paste customer return request here…"
                        value={singleText}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                          setSingleText(e.target.value)
                        }
                        maxLength={MAX_CHAR}
                        disabled={isSubmitting}
                      />
                    </div>

                    <div className="rounded-r-md border-l-2 border-neutral-400 bg-neutral-50/50 p-3 text-xs text-neutral-600">
                      <strong>Privacy &amp; Security Shield:</strong> Personal
                      identifiers (Sri Lankan NIC, Phone numbers, Card details,
                      Email, and physical addresses) are automatically redacted
                      prior to AI root-cause analysis.
                    </div>

                    {singleError && (
                      <div className="rounded-md border border-red-200/50 bg-red-50 p-3 text-sm text-red-600">
                        {singleError}
                      </div>
                    )}

                    <Button
                      type="submit"
                      disabled={isSubmitting || !singleText.trim()}
                      className="w-full sm:w-auto"
                    >
                      {isSubmitting && <Spinner className="mr-2" />}
                      {isSubmitting ? 'Analysing…' : 'Analyse Return'}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Live Reasoning Steps Panel */}
              {(isSubmitting || visibleSteps.length > 0) && !singleOutput && (
                <Card className="overflow-hidden">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b bg-neutral-50/50 px-5 py-3">
                    <CardTitle className="text-sm font-semibold text-neutral-800">
                      Live Reasoning Steps
                    </CardTitle>
                    {isSubmitting && (
                      <span className="animate-pulse font-mono text-[11px] text-neutral-400">
                        running…
                      </span>
                    )}
                  </CardHeader>
                  <CardContent className="p-0">
                    <ol className="divide-y divide-neutral-100">
                      {visibleSteps.map((stepIdx) => {
                        const stage = REASONING_STAGES[stepIdx];
                        if (!stage) return null;
                        const colors = AGENT_COLORS[stage.agent] ?? {
                          dot: 'bg-neutral-400',
                          label: 'text-neutral-600',
                        };
                        const isLast =
                          stepIdx === visibleSteps[visibleSteps.length - 1] &&
                          isSubmitting;
                        return (
                          <li
                            key={stepIdx}
                            className="flex items-start gap-3 px-5 py-3"
                          >
                            <div className="mt-0.5 flex shrink-0 flex-col items-center">
                              <span
                                className={`h-2 w-2 rounded-full ${
                                  isLast
                                    ? 'animate-pulse ring-2 ring-offset-1'
                                    : ''
                                } ${colors.dot}`}
                              />
                            </div>
                            <div className="flex min-w-0 flex-1 items-start gap-2">
                              <stage.Icon
                                className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${colors.label}`}
                                strokeWidth={1.75}
                              />
                              <div className="min-w-0">
                                <p
                                  className={`mb-0.5 text-[10px] font-semibold uppercase tracking-widest ${colors.label}`}
                                >
                                  {stage.agent}
                                </p>
                                <p className="text-sm leading-snug text-neutral-700">
                                  {stage.step}
                                </p>
                              </div>
                            </div>
                            {!isLast && (
                              <svg
                                className="mt-1 h-4 w-4 shrink-0 text-emerald-500"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth={2.5}
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            )}
                          </li>
                        );
                      })}
                    </ol>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Bulk Upload Tab */}
          <TabsContent value="bulk">
            <Card>
              <CardContent className="space-y-6 p-6">
                <div className="rounded-lg border-2 border-dashed border-neutral-300 p-8 text-center transition-colors hover:border-neutral-400">
                  <Input
                    type="file"
                    accept=".csv"
                    id="csvUpload"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="csvUpload"
                    className="block cursor-pointer space-y-2"
                  >
                    <svg
                      className="mx-auto h-12 w-12 text-neutral-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="text-sm font-medium text-neutral-700">
                      {csvFile
                        ? csvFile.name
                        : 'Click to select or drag and drop a returns CSV'}
                    </div>
                    <p className="text-xs text-neutral-500">
                      Supports up to 5,000 rows. UTF-8 encoded with 'text'
                      column.
                    </p>
                  </label>
                </div>

                {/* Preview Table */}
                {previewRows.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-neutral-800">
                      CSV Preview (First 5 Rows)
                    </h3>
                    <div className="overflow-x-auto rounded-md border">
                      <table className="min-w-full text-left text-xs">
                        <thead className="border-b bg-neutral-50">
                          <tr>
                            {Object.keys(previewRows[0]).map((h) => (
                              <th
                                key={h}
                                className="px-3 py-2 font-medium capitalize text-neutral-600"
                              >
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {previewRows.map((row, idx) => (
                            <tr key={idx} className="hover:bg-neutral-50">
                              {Object.values(row).map((val: unknown, cIdx) => (
                                <td
                                  key={cIdx}
                                  className="max-w-xs truncate px-3 py-2 text-neutral-700"
                                >
                                  {val || '—'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Validation Warnings */}
                {rowErrors.length > 0 && (
                  <div className="space-y-2 rounded-md border border-amber-200/50 bg-amber-50 p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wide text-amber-800">
                      Validation Warnings ({rowErrors.length})
                    </h4>
                    <ul className="list-inside list-disc space-y-1 text-xs text-amber-700">
                      {rowErrors.map((err, idx) => (
                        <li key={idx}>
                          Row {err.row}: <strong>{err.field}</strong> —{' '}
                          {err.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {csvFile && (
                  <Button onClick={handleBulkSubmit} disabled={isUploading}>
                    {isUploading && <Spinner className="mr-2" />}
                    {isUploading ? 'Uploading Batch…' : 'Start Batch Analysis'}
                  </Button>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
};

export default SubmitReturnPage;
