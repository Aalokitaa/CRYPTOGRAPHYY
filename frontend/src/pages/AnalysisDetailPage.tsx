import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  fetchAnalysisDetail, 
  getReportDownloadUrl 
} from '@/lib/api';
import { 
  formatBytes, 
  formatPercent, 
  truncateHash 
} from '@/lib/utils';
import { 
  Download, 
  Search, 
  ExternalLink,
  ShieldAlert,
  Network,
  Copy,
  Check,
  AlertTriangle
} from 'lucide-react';
import { PrimitiveBadge } from '@/components/ui/PrimitiveBadge';
import { ConfidenceBar } from '@/components/ui/ConfidenceBar';
import { UnsupportedIsaWarning, ErrorState, FilteredZeroState } from '@/components/ui/StateViews';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';

interface RecoveredFunction {
  id: string;
  hex_address: string;
  name?: string;
  size: number;
  primitive: string;
  confidence: number;
  constants_hit?: string[];
}

export const AnalysisDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => (id ? fetchAnalysisDetail(id) : null),
    enabled: !!id,
  });

  const [primitiveFilter, setPrimitiveFilter] = useState('ALL');
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [searchAddr, setSearchAddr] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);
  const [selectedRowId, setSelectedRowId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="p-12 text-center text-[12px] font-mono text-text-disabled">
        Reading binary sections and recovering function boundaries...
      </div>
    );
  }

  if (error || !analysis) {
    return <ErrorState title="Analysis Record Not Found" errorDetail={`Binary analysis record for target ID '${id}' was not located.`} />;
  }

  const isUnsupportedIsa = analysis.isa.toLowerCase().includes('xtensa');

  // Filter functions table
  const functions = (analysis.functions || []).filter((fn) => {
    const matchesPrim = primitiveFilter === 'ALL' || fn.primitive === primitiveFilter;
    const matchesConf = fn.confidence >= minConfidence;
    const matchesSearch = fn.hex_address.toLowerCase().includes(searchAddr.toLowerCase()) ||
                          fn.name?.toLowerCase().includes(searchAddr.toLowerCase());
    return matchesPrim && matchesConf && matchesSearch;
  });

  const columns: ColumnDef<RecoveredFunction>[] = [
    {
      key: 'hex_address',
      label: 'Address',
      width: 130,
      isSticky: true,
      isMono: true,
      render: (val: string) => (
        <span className="font-semibold text-accent tabular-nums">
          {val}
        </span>
      ),
    },
    {
      key: 'name',
      label: 'Symbol / Name',
      width: 200,
      isMono: true,
      render: (val: string, row: RecoveredFunction) => (
        <span className="text-text-primary truncate block" title={val || `sub_${row.hex_address.slice(2)}`}>
          {val || `sub_${row.hex_address.slice(2)}`}
        </span>
      ),
    },
    {
      key: 'size',
      label: 'Size',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => `${val} B`,
    },
    {
      key: 'primitive',
      label: 'Primitive',
      width: 130,
      render: (val: string) => <PrimitiveBadge primitive={val} showTagOnly={false} />,
    },
    {
      key: 'confidence',
      label: 'Confidence',
      width: 160,
      render: (val: number) => <ConfidenceBar confidence={val} threshold={minConfidence} />,
    },
    {
      key: 'constants_hit',
      label: 'Constants Hit',
      width: 150,
      render: (val: string[]) => {
        if (val && val.length > 0) {
          return (
            <span className="text-status-warning truncate block font-mono text-[12px]" title={val.join(', ')}>
              {val[0]}
            </span>
          );
        }
        return <span className="text-text-disabled font-mono text-[12px]">—</span>;
      },
    },
    {
      key: 'action',
      label: 'Drilldown',
      width: 90,
      align: 'right',
      render: (_: any, row: RecoveredFunction) => (
        <span className="inline-flex items-center gap-1 text-[12px] text-accent font-mono group-hover:underline">
          <span>Inspect</span>
          <ExternalLink className="w-3.5 h-3.5" strokeWidth={1.5} />
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Unsupported ISA Warning (if applicable) */}
      {isUnsupportedIsa && (
        <UnsupportedIsaWarning isa={analysis.isa} targetFile={analysis.filename} />
      )}

      {/* Top Header Row */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono font-bold text-[18px] text-text-primary">{analysis.filename}</span>
            <span className="px-2.5 py-0.5 rounded-[4px] bg-bg-raised border border-border-default font-mono text-[12px] text-accent font-semibold">
              {analysis.isa} {analysis.endianness === 'big' ? 'BE' : 'LE'}
            </span>
            <span className="px-2.5 py-0.5 rounded-[4px] bg-bg-raised border border-border-default font-mono text-[12px] text-text-secondary">
              -O2 (Inlined hints detected)
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[12px] text-text-secondary font-mono mt-1">
            <span>{analysis.format}</span>
            <span>•</span>
            <span>{formatBytes(analysis.file_size)}</span>
            <span>•</span>
            <span>Entry: {analysis.entrypoint}</span>
            <span>•</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(analysis.sha256);
                setCopiedHash(true);
                setTimeout(() => setCopiedHash(false), 1500);
              }}
              className="flex items-center gap-1.5 hover:text-text-primary cursor-pointer"
              title="Click to copy full SHA-256"
            >
              <span>SHA: {truncateHash(analysis.sha256)}</span>
              {copiedHash ? <Check className="w-3.5 h-3.5 text-status-success" strokeWidth={1.5} /> : <Copy className="w-3.5 h-3.5 text-text-disabled" strokeWidth={1.5} />}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <Link
            to="/protocol"
            className="flex items-center gap-1.5 px-3 py-2 bg-bg-raised border border-border-default text-text-primary hover:text-accent rounded-[4px] text-[12px] font-mono transition min-h-[44px] cursor-pointer"
          >
            <Network className="w-4 h-4" strokeWidth={1.5} />
            <span>Protocol Graph</span>
          </Link>
          <a
            href={getReportDownloadUrl(analysis.id, 'html')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-2 bg-bg-raised border border-border-default text-text-primary hover:text-accent rounded-[4px] text-[12px] font-mono transition min-h-[44px] cursor-pointer"
          >
            <Download className="w-4 h-4" strokeWidth={1.5} />
            <span>HTML</span>
          </a>
          <a
            href={getReportDownloadUrl(analysis.id, 'pdf')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-accent text-accent-on font-mono font-bold rounded-[4px] text-[12px] transition hover:bg-accent-hover min-h-[44px] cursor-pointer"
          >
            <Download className="w-4 h-4" strokeWidth={1.5} />
            <span>Export Report</span>
          </a>
        </div>
      </div>

      {/* Full-width Address-Space Entropy & Crypto-Density Strip */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2 font-mono text-[12px]">
        <div className="flex items-center justify-between text-[12px] text-text-secondary uppercase tracking-[0.04em]">
          <span>Address Space Entropy & Cryptographic Region Density</span>
          <span className="text-text-disabled">0x00000000 → 0x00400000</span>
        </div>
        <div className="h-7 w-full bg-bg-raised border border-border-default rounded-[4px] flex overflow-hidden cursor-crosshair">
          <div className="w-[18%] bg-prim-aes/20 border-r border-border-default relative group" title="Offset 0x0000-0x18000: AES & S-box Table">
            <span className="absolute inset-0 flex items-center justify-center text-[12px] font-bold text-prim-aes">[AES]</span>
          </div>
          <div className="w-[32%] bg-bg-raised border-r border-border-default" title="Non-crypto code & parsing logic" />
          <div className="w-[14%] bg-prim-sha256/20 border-r border-border-default relative group" title="SHA-256 Round Constants">
            <span className="absolute inset-0 flex items-center justify-center text-[12px] font-bold text-prim-sha256">[S256]</span>
          </div>
          <div className="w-[20%] bg-bg-raised border-r border-border-default" title="Standard C library / dynamic stubs" />
          <div className="w-[16%] bg-prim-hmac/20 relative group" title="HMAC Inner & Outer Pads">
            <span className="absolute inset-0 flex items-center justify-center text-[12px] font-bold text-prim-hmac">[HMC]</span>
          </div>
        </div>
      </div>

      {/* Split: Left 8 Columns (Function Table) vs Right 4 Columns (Distribution & Top Findings) (Max 2 Containers) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8 Columns: Function Table Container */}
        <div className="lg:col-span-8 border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-3 flex flex-col">
          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 font-mono text-[12px]">
            <div className="flex items-center gap-2">
              <span className="text-text-primary font-bold">{functions.length}</span>
              <span className="text-text-secondary">Functions Found</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-text-disabled absolute left-2.5 top-2.5" strokeWidth={1.5} />
                <input
                  type="text"
                  placeholder="Address or sub_..."
                  value={searchAddr}
                  onChange={(e) => setSearchAddr(e.target.value)}
                  className="bg-bg-raised border border-border-default rounded-[4px] pl-8 pr-2.5 py-1.5 text-[12px] font-mono text-text-primary outline-none focus:border-accent w-40 min-h-[36px]"
                />
              </div>

              {/* Primitive Filter Chips */}
              <select
                value={primitiveFilter}
                onChange={(e) => setPrimitiveFilter(e.target.value)}
                className="bg-bg-raised border border-border-default text-text-primary rounded-[4px] px-2.5 py-1.5 text-[12px] font-mono outline-none focus:border-accent min-h-[36px]"
              >
                <option value="ALL">All Primitives</option>
                <option value="AES">AES</option>
                <option value="DES">DES</option>
                <option value="RSA">RSA</option>
                <option value="ECC">ECC</option>
                <option value="SHA-256">SHA-256</option>
                <option value="HMAC">HMAC</option>
                <option value="ChaCha20">ChaCha20</option>
                <option value="Non-crypto">Non-crypto</option>
              </select>

              {/* Confidence Threshold */}
              <div className="flex items-center gap-2 text-text-secondary text-[12px] bg-bg-raised px-2.5 py-1 rounded-[4px] border border-border-default min-h-[36px]">
                <span>&gt;{Math.round(minConfidence * 100)}%</span>
                <input 
                  type="range" 
                  min="0" 
                  max="0.9" 
                  step="0.05" 
                  value={minConfidence} 
                  onChange={e => setMinConfidence(parseFloat(e.target.value))} 
                  className="w-16 accent-accent h-1.5 cursor-pointer" 
                />
              </div>
            </div>
          </div>

          {/* 28px Dense Function Table using DataTable */}
          {functions.length === 0 ? (
            <FilteredZeroState
              activeFiltersCount={searchAddr || primitiveFilter !== 'ALL' || minConfidence > 0 ? 1 : 0}
              onResetFilters={() => {
                setSearchAddr('');
                setPrimitiveFilter('ALL');
                setMinConfidence(0.5);
              }}
            />
          ) : (
            <DataTable
              columns={columns}
              data={functions}
              selectedId={selectedRowId}
              onRowClick={(row) => {
                setSelectedRowId(row.id);
                navigate(`/functions/${row.id}`);
              }}
              idKey="id"
            />
          )}
        </div>

        {/* Right 4 Columns: Distribution & Defensive Security Findings Container */}
        <div className="lg:col-span-4 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-5 font-mono text-[12px]">
          {/* Stacked Distribution Bar */}
          <div className="space-y-3">
            <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary block border-b border-border-default pb-1">
              Primitive Class Distribution
            </span>

            {/* Stacked Horizontal Bar */}
            <div className="h-5 w-full bg-bg-raised rounded-[2px] border border-border-default flex overflow-hidden">
              {Object.entries(analysis.primitive_counts || {}).map(([prim, count]) => {
                const total = analysis.total_functions || 1;
                const pct = (count / total) * 100;
                return (
                  <div
                    key={prim}
                    style={{ 
                      width: `${pct}%`, 
                      backgroundColor: `var(--primitive-${prim.toLowerCase().replace(/[^a-z0-9]/g, '')}, var(--border-strong))`
                    }}
                    title={`${prim}: ${count} (${pct.toFixed(1)}%)`}
                    className="h-full border-r border-bg-surface last:border-0"
                  />
                );
              })}
            </div>

            {/* Breakdown List */}
            <div className="space-y-2 pt-1">
              {Object.entries(analysis.primitive_counts || {}).map(([prim, count]) => (
                <div key={prim} className="flex items-center justify-between text-[12px]">
                  <div className="flex items-center gap-2">
                    <PrimitiveBadge primitive={prim} showTagOnly={true} />
                    <span className="text-text-secondary">{prim}</span>
                  </div>
                  <span className="font-bold text-text-primary tabular-nums">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Defensive Findings List */}
          <div className="space-y-3 pt-3 border-t border-border-default">
            <div className="flex items-center justify-between border-b border-border-default pb-1">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Defensive Audit Findings
              </span>
              <span className="text-[12px] font-bold text-status-warning">
                {analysis.advisories?.length || 0} Observations
              </span>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {(!analysis.advisories || analysis.advisories.length === 0) ? (
                <div className="p-3 bg-bg-raised rounded-[4px] text-text-disabled text-center text-[12px]">
                  No weak or legacy cryptographic algorithms detected.
                </div>
              ) : (
                analysis.advisories.map((adv) => (
                  <div key={adv.id} className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-text-primary text-[12px] truncate max-w-[200px]">{adv.title}</span>
                      <span className={`text-[12px] font-bold px-1.5 py-0.5 rounded-[4px] ${adv.severity === 'CRITICAL' ? 'bg-status-danger/20 text-status-danger' : 'bg-status-warning/20 text-status-warning'}`}>
                        {adv.severity}
                      </span>
                    </div>
                    <p className="text-[12px] text-text-secondary leading-snug font-sans">{adv.risk_summary}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
