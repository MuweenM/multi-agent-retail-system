import { useMemo, useState } from 'react';
import { AlertCircle, ArrowUpRight, Search, SlidersHorizontal } from 'lucide-react';
import mockEvidence from '@/mocks/evidenceSearch.json';
import { retrieveEvidence } from '@/lib/api';
import type { EvidenceItem, EvidenceOutput } from '@/types/contracts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';

type Method = 'bm25' | 'tfidf' | 'dense' | 'hybrid';
type FilterKey = 'source_type' | 'product_id' | 'supplier_id' | 'date_range';

const METHOD_LABELS: Record<Method, string> = {
  bm25: 'Keyword BM25',
  tfidf: 'TF-IDF',
  dense: 'Semantic',
  hybrid: 'Hybrid',
};

const SOURCE_TYPES = ['all', 'review', 'return_history', 'supplier_note', 'catalog'];
const PRODUCTS = ['all', 'P-014', 'P-027', 'P-009'];
const SUPPLIERS = ['all', 'S-03', 'S-08', 'S-11'];
const DATE_RANGES = ['all', '7 days', '30 days', '90 days'];

const mockOutput = mockEvidence as EvidenceOutput & { by_method: Record<Method, string[]> };
const mockMethodResults = (Object.keys(METHOD_LABELS) as Method[]).reduce<Record<Method, EvidenceItem[]>>((results, method) => {
  const byId = new Map(mockOutput.evidence.map((item) => [item.source_id, item]));
  results[method] = mockOutput.by_method[method].map((id) => byId.get(id)).filter((item): item is EvidenceItem => Boolean(item));
  return results;
}, {} as Record<Method, EvidenceItem[]>);

function sourceLabel(sourceType: string): string {
  return sourceType.replaceAll('_', ' ');
}

function HighlightedTerms({ item }: { item: EvidenceItem }) {
  const terms = new Set(item.matched_terms.map((term) => term.toLowerCase()));
  return (
    <span>
      {item.snippet.split(/(\s+)/).map((part, index) => {
        const clean = part.replace(/[.,!?;:()[\]]/g, '').toLowerCase();
        return terms.has(clean) ? (
          <mark key={`${part}-${index}`} className="rounded bg-amber-100 px-0.5 text-neutral-950">
            {part}
          </mark>
        ) : (
          <span key={`${part}-${index}`}>{part}</span>
        );
      })}
    </span>
  );
}

function ResultRow({ item }: { item: EvidenceItem }) {
  const score = Math.max(0, Math.min(1, item.relevance_score));
  return (
    <div className="border-b border-neutral-200 px-5 py-4 last:border-b-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="rounded-full border-neutral-200 bg-neutral-50 font-mono text-[10px] uppercase text-neutral-600">
              {sourceLabel(item.source_type)}
            </Badge>
            <span className="font-mono text-[11px] text-neutral-400">{item.source_id}</span>
            {item.label_hint && <Badge className="rounded-full bg-neutral-900 text-[10px] text-white">{sourceLabel(item.label_hint)}</Badge>}
          </div>
          <h3 className="text-sm font-semibold text-neutral-950">{item.title}</h3>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-neutral-600"><HighlightedTerms item={item} /></p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {item.matched_terms.map((term) => (
              <Badge key={term} variant="secondary" className="rounded-full font-mono text-[10px]">{term}</Badge>
            ))}
          </div>
        </div>
        <div className="w-24 shrink-0 text-right">
          <div className="font-mono text-xs font-semibold text-neutral-900">{score.toFixed(2)}</div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-neutral-100">
            <div className="h-full rounded-full bg-neutral-900" style={{ width: `${score * 100}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

function MethodRail({ output, methodResults }: { output: EvidenceOutput; methodResults: Record<Method, EvidenceItem[]> }) {
  return (
    <Card className="h-fit rounded-lg border border-neutral-200 bg-white shadow-none">
      <CardHeader className="border-b border-neutral-200 pb-4">
        <CardTitle className="text-sm">Method comparison</CardTitle>
        <CardDescription className="text-xs">Top five for the same query</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5 pt-5">
        {(Object.keys(METHOD_LABELS) as Method[]).map((method) => {
          const results = methodResults[method];
          return (
            <div key={method}>
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-neutral-900">{METHOD_LABELS[method]}</span>
                <Badge variant={method === output.method ? 'default' : 'outline'} className="rounded-full px-1.5 py-0 font-mono text-[9px]">
                  {method === output.method ? 'active' : method}
                </Badge>
              </div>
              <div className="space-y-1.5">
                {results.slice(0, 5).map((item, index) => {
                  return (
                    <div key={`${method}-${item.source_id}`} className="flex items-center gap-2 text-[11px]">
                      <span className="w-3 font-mono text-neutral-400">{index + 1}</span>
                      <span className="min-w-0 flex-1 truncate text-neutral-600">{item.title}</span>
                      <span className="font-mono text-neutral-400">{item.relevance_score.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export default function EvidenceSearchPage() {
  const [query, setQuery] = useState(mockOutput.query);
  const [submittedQuery, setSubmittedQuery] = useState(mockOutput.query);
  const [method, setMethod] = useState<Method>('hybrid');
  const [filters, setFilters] = useState<Record<FilterKey, string>>({ source_type: 'all', product_id: 'all', supplier_id: 'all', date_range: 'all' });
  const [output, setOutput] = useState<EvidenceOutput>(mockOutput);
  const [methodResults, setMethodResults] = useState<Record<Method, EvidenceItem[]>>(mockMethodResults);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredEvidence = useMemo(() => output.evidence.filter((item) => {
    const metadata = item.metadata ?? {};
    return (filters.source_type === 'all' || item.source_type === filters.source_type)
      && (filters.product_id === 'all' || metadata.product_id === filters.product_id)
      && (filters.supplier_id === 'all' || metadata.supplier_id === filters.supplier_id);
  }), [filters, output.evidence]);

  const runSearch = async () => {
    const nextQuery = query.trim();
    if (!nextQuery) return;
    setLoading(true);
    setError(null);
    setSubmittedQuery(nextQuery);
    try {
      const apiFilters = {
        source_type: filters.source_type === 'all' ? undefined : filters.source_type,
        product_id: filters.product_id === 'all' ? undefined : filters.product_id,
        supplier_id: filters.supplier_id === 'all' ? undefined : filters.supplier_id,
        date_range: filters.date_range === 'all' ? undefined : filters.date_range,
      };
      const results = await Promise.all((Object.keys(METHOD_LABELS) as Method[]).map((searchMethod) => retrieveEvidence({ query: nextQuery, method: searchMethod, filters: apiFilters })));
      const nextMethodResults = results.reduce<Record<Method, EvidenceItem[]>>((allResults, result, index) => {
        allResults[(Object.keys(METHOD_LABELS) as Method[])[index]] = result.evidence;
        return allResults;
      }, {} as Record<Method, EvidenceItem[]>);
      setMethodResults(nextMethodResults);
      setOutput(results[(Object.keys(METHOD_LABELS) as Method[]).indexOf(method)]);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : 'Evidence search failed.');
    } finally {
      setLoading(false);
    }
  };

  const setFilter = (key: FilterKey, value: string) => setFilters((current) => ({ ...current, [key]: value }));

  return (
    <section className="min-h-[calc(100vh-52px)] bg-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-5">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-mono uppercase tracking-[0.18em] text-neutral-400">
              <Search className="h-3.5 w-3.5" /> Agent 3 / Retrieval
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-neutral-950">Evidence search</h1>
            <p className="mt-1 text-sm text-neutral-500">Find the signals behind a return decision.</p>
          </div>
          <Badge variant="outline" className="rounded-full border-neutral-200 bg-neutral-50 px-2.5 py-1 font-mono text-[10px] text-neutral-500">
            {output.total_results} results · {output.latency_ms} ms
          </Badge>
        </div>

        <div className="mb-6 space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => { if (event.key === 'Enter') void runSearch(); }}
              placeholder="Search returns, reviews, suppliers..."
              className="h-10 rounded-full border-neutral-200 px-4 text-sm"
              aria-label="Evidence search query"
            />
            <Button onClick={() => void runSearch()} disabled={loading || !query.trim()} className="h-10 rounded-full bg-black px-5 text-sm hover:bg-neutral-800">
              {loading ? <Spinner className="mr-2" /> : <Search className="mr-2 h-4 w-4" />}
              Search
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <ToggleGroup type="single" value={method} onValueChange={(value) => { if (value) setMethod(value as Method); }} variant="outline" size="sm" className="rounded-full border border-neutral-200 bg-neutral-50 p-0.5">
              {(Object.keys(METHOD_LABELS) as Method[]).map((option) => <ToggleGroupItem key={option} value={option} className="rounded-full px-3 text-xs data-[state=on]:bg-black data-[state=on]:text-white">{METHOD_LABELS[option]}</ToggleGroupItem>)}
            </ToggleGroup>
            <div className="ml-auto flex items-center gap-1.5 text-xs text-neutral-400"><SlidersHorizontal className="h-3.5 w-3.5" /> Filters</div>
            {([['source_type', 'Source type', SOURCE_TYPES], ['product_id', 'Product', PRODUCTS], ['supplier_id', 'Supplier', SUPPLIERS], ['date_range', 'Date range', DATE_RANGES]] as const).map(([key, label, options]) => (
              <Select key={key} value={filters[key]} onValueChange={(value) => setFilter(key, value)}>
                <SelectTrigger size="sm" className="rounded-full border-neutral-200 bg-white text-xs"><SelectValue aria-label={label} /></SelectTrigger>
                <SelectContent><SelectItem value="all">{label}: All</SelectItem>{options.slice(1).map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}</SelectContent>
              </Select>
            ))}
          </div>
        </div>

        {output.corrected_query && output.corrected_query !== submittedQuery && (
          <div className="mb-5 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <ArrowUpRight className="h-4 w-4 shrink-0" /> Showing results for <span className="font-semibold">{output.corrected_query}</span> <span className="text-amber-700">(you typed {submittedQuery})</span>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
          <Card className="rounded-lg border border-neutral-200 bg-white shadow-none">
            <CardHeader className="border-b border-neutral-200 pb-4"><CardTitle className="text-sm">Retrieved evidence</CardTitle><CardDescription className="text-xs">Ranked by {METHOD_LABELS[method]}</CardDescription></CardHeader>
            <CardContent className="p-0">
              {error ? <Empty className="min-h-64 border-0"><EmptyMedia variant="icon"><AlertCircle /></EmptyMedia><EmptyHeader><EmptyTitle>Search unavailable</EmptyTitle><EmptyDescription>{error}</EmptyDescription></EmptyHeader></Empty> : loading ? <div className="flex min-h-64 items-center justify-center"><Spinner className="size-6" /></div> : filteredEvidence.length === 0 ? <Empty className="min-h-64 border-0"><EmptyMedia variant="icon"><Search /></EmptyMedia><EmptyHeader><EmptyTitle>No evidence found</EmptyTitle><EmptyDescription>Try a broader query or remove a filter.</EmptyDescription></EmptyHeader></Empty> : filteredEvidence.map((item) => <ResultRow key={item.source_id} item={item} />)}
            </CardContent>
          </Card>
          <MethodRail output={output} methodResults={methodResults} />
        </div>
      </div>
    </section>
  );
}