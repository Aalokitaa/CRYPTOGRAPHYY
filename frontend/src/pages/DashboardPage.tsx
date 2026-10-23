import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  ArrowRight, 
  CheckCircle2, 
  Copy, 
  Check 
} from 'lucide-react';
import { fetchAnalyses, fetchToolchainStatus } from '@/lib/api';
import { formatBytes, truncateHash } from '@/lib/utils';
import { StatStrip } from '@/components/ui/StatStrip';
import { PrimitiveBadge } from '@/components/ui/PrimitiveBadge';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';

interface FirmwareItem {
  id: string;
  filename: string;
  isa: string;
  endianness: string;
  sha256: string;
  file_size: number;
  total_functions: number;
  primitive_counts: Record<string, number>;
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: analyses, isLoading: loadingAnalyses } = useQuery({
    queryKey: ['analyses'],
    queryFn: fetchAnalyses,
  });

  const { data: toolchain } = useQuery({
    queryKey: ['toolchain'],
    queryFn: fetchToolchainStatus,
  });

  const [copiedHash, setCopiedHash] = React.useState<string | null>(null);

  const copyHash = (hash: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 1500);
  };

  const statItems = [
    { label: 'Firmware Analyzed', value: '214', subtext: 'Target binaries' },
    { label: 'Functions Classified', value: '48,912', subtext: 'Symbol-less recovered' },
    { label: 'Datasets Available', value: '3', subtext: '50 multi-ISA matrix' },
    { label: 'Best Model F1', value: '0.955', subtext: 'Transformer (8 heads)', highlight: true },
  ];

  const columns: ColumnDef<FirmwareItem>[] = [
    {
      key: 'filename',
      label: 'Target Filename',
      width: 190,
      isSticky: true,
      render: (val: string) => (
        <span className="font-bold text-text-primary truncate block" title={val}>
          {val}
        </span>
      ),
    },
    {
      key: 'isa',
      label: 'Architecture',
      width: 130,
      isMono: true,
      render: (_: any, row: FirmwareItem) => (
        <span>
          {row.isa}{' '}
          <span className="text-[12px] text-text-disabled">
            {row.endianness === 'big' ? 'BE' : 'LE'}
          </span>
        </span>
      ),
    },
    {
      key: 'sha256',
      label: 'SHA-256 Digest',
      width: 130,
      isMono: true,
      render: (val: string) => (
        <button
          onClick={(e) => copyHash(val, e)}
          className="inline-flex items-center gap-1.5 text-text-secondary hover:text-text-primary text-[12px] group cursor-pointer"
          title="Click to copy full SHA-256"
        >
          <span>{truncateHash(val)}</span>
          {copiedHash === val ? (
            <Check className="w-3.5 h-3.5 text-status-success shrink-0" strokeWidth={1.5} />
          ) : (
            <Copy className="w-3.5 h-3.5 text-text-disabled opacity-0 group-hover:opacity-100 shrink-0" strokeWidth={1.5} />
          )}
        </button>
      ),
    },
    {
      key: 'file_size',
      label: 'Size',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => formatBytes(val),
    },
    {
      key: 'total_functions',
      label: 'Functions',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => val.toLocaleString(),
    },
    {
      key: 'primitive_counts',
      label: 'Top Finding',
      width: 120,
      render: (counts: Record<string, number>) => {
        const topPrim = Object.keys(counts || {})[0] || 'AES';
        return <PrimitiveBadge primitive={topPrim} showTagOnly={false} />;
      },
    },
    {
      key: 'action',
      label: 'Action',
      width: 80,
      align: 'right',
      render: (_: any, row: FirmwareItem) => (
        <span className="inline-flex items-center gap-1 text-[12px] text-accent font-mono group-hover:underline">
          <span>Inspect</span>
          <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Slim Bordered Stat Strip with Dividers */}
      <StatStrip items={statItems} />

      {/* Main Grid: Left 8 Columns (Table) vs Right 4 Columns (Tools/Jobs/Checklist) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8 Columns: Recent Firmware Analyses Table */}
        <div className="lg:col-span-8 flex flex-col space-y-2">
          <div className="h-10 px-4 border border-border-default bg-bg-surface rounded-[6px] flex items-center justify-between">
            <span className="text-[12px] font-mono font-semibold uppercase tracking-[0.04em] text-text-primary">
              Recent Firmware Analyses
            </span>
            <Link 
              to="/analyses" 
              className="text-[12px] font-mono text-accent hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View All 214</span>
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
            </Link>
          </div>

          <DataTable
            columns={columns}
            data={(analyses || []).slice(0, 6)}
            onRowClick={(row) => navigate(`/analysis/${row.id}`)}
            emptyMessage={loadingAnalyses ? 'Loading firmware target catalog...' : 'No firmware analyzed yet.'}
          />
        </div>

        {/* Right 4 Columns: Toolchain Status, Running Jobs & 4-Step Checklist */}
        <div className="lg:col-span-4 space-y-4">
          {/* Toolchain Health Status Module */}
          <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2.5">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-mono font-semibold uppercase tracking-[0.04em] text-text-primary">
                Toolchain Health Status
              </span>
              <span className="text-[12px] font-mono text-status-success flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-status-success" />
                <span>Active</span>
              </span>
            </div>

            <div className="space-y-1.5 text-[12px] font-mono">
              <div className="flex items-center justify-between py-1 border-b border-border-default/50">
                <span className="text-text-secondary">gcc-aarch64</span>
                <span className="text-status-success font-semibold">Installed</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-border-default/50">
                <span className="text-text-secondary">arm-linux-gnueabihf</span>
                <span className="text-status-success font-semibold">Installed</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-border-default/50">
                <span className="text-text-secondary">mips-linux-gnu</span>
                <span className="text-status-warning font-semibold">Synthetic Fallback</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-text-secondary">riscv64-linux-gnu</span>
                <span className="text-status-success font-semibold">Installed</span>
              </div>
            </div>

            <div className="pt-1 text-[12px] font-mono text-text-disabled">
              Missing MIPS compiler: <code className="text-accent">sudo apt-get install gcc-mips-linux-gnu</code>
            </div>
          </div>

          {/* First-Run Workflow Checklist */}
          <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2.5">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-mono font-semibold uppercase tracking-[0.04em] text-text-primary">
                Workflow Verification
              </span>
              <span className="text-[12px] font-mono text-text-disabled">4 / 4 Complete</span>
            </div>

            <div className="space-y-2 text-[12px]">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-status-success shrink-0 mt-0.5" strokeWidth={1.5} />
                <div>
                  <span className="font-semibold text-text-primary block text-[12px]">1. Toolchain Probe</span>
                  <span className="text-text-secondary text-[12px]">Multi-arch cross compilers identified</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-status-success shrink-0 mt-0.5" strokeWidth={1.5} />
                <div>
                  <span className="font-semibold text-text-primary block text-[12px]">2. Dataset Matrix</span>
                  <span className="text-text-secondary text-[12px]">50 multi-ISA binaries synthesized (v1.0.0)</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-status-success shrink-0 mt-0.5" strokeWidth={1.5} />
                <div>
                  <span className="font-semibold text-text-primary block text-[12px]">3. Model Training</span>
                  <span className="text-text-secondary text-[12px]">Transformer & RF trained (Macro F1: 0.955)</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-status-success shrink-0 mt-0.5" strokeWidth={1.5} />
                <div>
                  <span className="font-semibold text-text-primary block text-[12px]">4. Firmware Analysis</span>
                  <span className="text-text-secondary text-[12px]">Target binaries reverse-engineered</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
