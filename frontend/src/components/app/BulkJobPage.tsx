import React, { useState, useEffect, useRef } from 'react';
import { BulkJobStatus, BulkResultRow } from '@/types/contracts';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyContent,
} from '@/components/ui/empty';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Download,
  Search,
} from 'lucide-react';
import {
  uploadBulk,
  getBulkStatus,
  getBulkResults,
  exportBulkCsv,
} from '@/lib/api';

function DecisionChip({ decision }: { decision: string }) {
  const map: Record<string, { cls: string; icon: React.ReactNode }> = {
    approve: {
      cls: 'border-emerald-200 bg-emerald-50 text-emerald-800',
      icon: <CheckCircle className="h-3 w-3" />,
    },
    reject: {
      cls: 'border-rose-200 bg-rose-50 text-rose-800',
      icon: <XCircle className="h-3 w-3" />,
    },
    escalate: {
      cls: 'border-amber-200 bg-amber-50 text-amber-800',
      icon: <AlertTriangle className="h-3 w-3" />,
    },
    request_info: {
      cls: 'border-sky-200 bg-sky-50 text-sky-800',
      icon: <HelpCircle className="h-3 w-3" />,
    },
  };
  const cfg = map[decision] ?? {
    cls: 'border-neutral-200 bg-neutral-100 text-neutral-700',
    icon: null,
  };
  return (
    <Badge
      variant="outline"
      className={`flex w-fit items-center gap-1 rounded-full font-mono text-[10px] ${cfg.cls}`}
    >
      {cfg.icon}
      {decision}
    </Badge>
  );
}

export default function BulkJobPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<BulkJobStatus | null>(null);
  const [results, setResults] = useState<BulkResultRow[]>([]);
  const [filter, setFilter] = useState('');
  const [loadingResults, setLoadingResults] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const s = await getBulkStatus(jobId);
        setStatus(s);
        if (s.status === 'completed' || s.status === 'failed') {
          clearPoll();
          if (s.status === 'completed') {
            setLoadingResults(true);
            const r = await getBulkResults(jobId, 1, 200);
            setResults(r.results);
            setLoadingResults(false);
          }
        }
      } catch {
        clearPoll();
      }
    };

    poll();
    pollRef.current = setInterval(poll, 3000);
    return clearPoll;
  }, [jobId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setUploadError(null);
      setJobId(null);
      setStatus(null);
      setResults([]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const res = await uploadBulk(file);
      setJobId(res.job_id);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const progress =
    status && status.total_rows > 0
      ? Math.round((status.processed_rows / status.total_rows) * 100)
      : 0;

  const filteredResults = results.filter(
    (r) =>
      !filter ||
      r.decision.toLowerCase().includes(filter.toLowerCase()) ||
      r.root_cause.toLowerCase().includes(filter.toLowerCase()) ||
      r.return_id.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight text-neutral-950">
          Bulk Return Processing
        </h1>
        <p className="text-sm text-neutral-500">
          Upload a CSV to process up to 5,000 returns asynchronously.
        </p>
      </div>

      {/* Upload Card */}
      <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
        <CardHeader className="p-5 pb-3">
          <CardTitle className="text-sm font-semibold text-neutral-900">
            Upload CSV
          </CardTitle>
          <CardDescription className="text-xs text-neutral-400">
            Required column: <code className="font-mono">text</code>. Optional:{' '}
            <code className="font-mono">order_id, product_id, store_id</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 p-5 pt-0">
          <label
            htmlFor="bulk-csv-input"
            className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-neutral-200 bg-neutral-50 px-6 py-10 text-center transition-colors hover:border-neutral-400"
          >
            <span className="mb-1 text-sm font-medium text-neutral-700">
              {file ? file.name : 'Click to select a CSV file'}
            </span>
            <span className="text-xs text-neutral-400">
              UTF-8, up to 5,000 rows
            </span>
            <Input
              id="bulk-csv-input"
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>

          {uploadError && (
            <p className="text-xs text-rose-600">{uploadError}</p>
          )}

          {file && !jobId && (
            <Button
              id="bulk-upload-btn"
              size="sm"
              disabled={uploading}
              onClick={handleUpload}
              className="h-8 rounded-full bg-black px-4 text-xs text-white hover:bg-neutral-800"
            >
              {uploading ? (
                <Spinner className="h-3 w-3 text-white" />
              ) : (
                'Start Batch Analysis'
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Progress Card */}
      {status && (
        <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-neutral-900">
                Job <span className="font-mono text-neutral-500">{jobId}</span>
              </CardTitle>
              <Badge
                variant="outline"
                className={`rounded-full font-mono text-[10px] ${
                  status.status === 'completed'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    : status.status === 'failed'
                      ? 'border-rose-200 bg-rose-50 text-rose-800'
                      : 'border-sky-200 bg-sky-50 text-sky-800'
                }`}
              >
                {status.status === 'processing' && (
                  <Spinner className="mr-1 h-2.5 w-2.5" />
                )}
                {status.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 p-5 pt-0">
            <Progress value={progress} className="h-2" />
            <div className="flex items-center justify-between font-mono text-xs text-neutral-500">
              <span>
                {status.processed_rows} / {status.total_rows} rows
              </span>
              <span className="text-rose-600">{status.failed_rows} failed</span>
            </div>
            {status.summary?.executive_summary && (
              <div className="rounded-lg bg-neutral-50 p-3 text-xs leading-relaxed text-neutral-600">
                {status.summary.executive_summary}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Table */}
      {(results.length > 0 || loadingResults) && (
        <Card className="rounded-xl border border-neutral-200 bg-white shadow-none">
          <CardHeader className="p-5 pb-3">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-sm font-semibold text-neutral-900">
                Results ({results.length})
              </CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-neutral-400" />
                  <Input
                    id="bulk-results-filter"
                    placeholder="Filter by decision…"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="h-8 w-48 rounded-full border-neutral-200 pl-7 text-xs"
                  />
                </div>
                <Button
                  id="bulk-export-btn"
                  size="sm"
                  variant="outline"
                  onClick={() => jobId && exportBulkCsv(jobId)}
                  className="h-8 rounded-full border-neutral-200 px-3 text-xs"
                >
                  <Download className="mr-1.5 h-3 w-3" />
                  Export CSV
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loadingResults ? (
              <div className="flex items-center justify-center py-12">
                <Spinner className="h-5 w-5 text-neutral-400" />
              </div>
            ) : filteredResults.length === 0 ? (
              <Empty className="py-12">
                <EmptyHeader>
                  <EmptyTitle>No results match your filter</EmptyTitle>
                  <EmptyDescription>Try clearing the filter.</EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setFilter('')}
                    className="rounded-full text-xs"
                  >
                    Clear filter
                  </Button>
                </EmptyContent>
              </Empty>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-neutral-200">
                    <TableHead className="font-mono text-[10px] uppercase tracking-wider text-neutral-400">
                      Return ID
                    </TableHead>
                    <TableHead className="font-mono text-[10px] uppercase tracking-wider text-neutral-400">
                      Decision
                    </TableHead>
                    <TableHead className="font-mono text-[10px] uppercase tracking-wider text-neutral-400">
                      Root Cause
                    </TableHead>
                    <TableHead className="font-mono text-[10px] uppercase tracking-wider text-neutral-400">
                      Confidence
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResults.map((row, i) => (
                    <TableRow
                      key={i}
                      className="border-neutral-200 hover:bg-neutral-50"
                    >
                      <TableCell className="font-mono text-xs text-neutral-700">
                        {row.return_id}
                      </TableCell>
                      <TableCell>
                        <DecisionChip decision={row.decision} />
                      </TableCell>
                      <TableCell className="text-xs text-neutral-600">
                        {row.root_cause.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-neutral-600">
                        {Math.round(row.confidence * 100)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
