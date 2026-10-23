import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { fetchAblation, fetchRobustness } from '@/lib/api';
import { formatPercent } from '@/lib/utils';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';

interface AblationRow {
  name: string;
  f1: number;
  accuracy: number;
  latency: number;
}

interface DegradationDeltaRow {
  opt: string;
  gccDelta: number;
  clangDelta: number;
  note: string;
}

export const AblationRobustnessPage: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);

  const { data: ablation, refetch: refetchAblation } = useQuery({
    queryKey: ['ablation'],
    queryFn: () => fetchAblation(false),
  });

  const { data: robustness, refetch: refetchRobustness } = useQuery({
    queryKey: ['robustness'],
    queryFn: () => fetchRobustness(false),
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAblation(true);
    await fetchRobustness(true);
    await refetchAblation();
    await refetchRobustness();
    setRefreshing(false);
  };

  const ablationRows: AblationRow[] = [
    { name: 'Byte only', f1: 0.724, accuracy: 0.741, latency: 0.8 },
    { name: 'Instruction only', f1: 0.885, accuracy: 0.892, latency: 1.1 },
    { name: 'Instruction + CFG', f1: 0.928, accuracy: 0.934, latency: 1.6 },
    { name: 'Instruction + DFG', f1: 0.946, accuracy: 0.951, latency: 1.8 },
    { name: 'All features', f1: 0.964, accuracy: 0.968, latency: 2.2 },
  ];

  const degradationCurves = [
    { opt: 'O0', gcc: 0.978, clang: 0.974 },
    { opt: 'O1', gcc: 0.965, clang: 0.960 },
    { opt: 'O2', gcc: 0.952, clang: 0.948 },
    { opt: 'O3', gcc: 0.938, clang: 0.932 },
    { opt: 'Os', gcc: 0.925, clang: 0.919 },
  ];

  const degradationDeltas: DegradationDeltaRow[] = [
    { opt: 'O0 → O1', gccDelta: -1.3, clangDelta: -1.4, note: 'Basic block scheduling' },
    { opt: 'O1 → O2', gccDelta: -1.3, clangDelta: -1.2, note: 'Instruction reordering & loop unrolling' },
    { opt: 'O2 → O3', gccDelta: -1.4, clangDelta: -1.6, note: 'Aggressive inlining & SIMD vectorization' },
    { opt: 'O2 → Os', gccDelta: -2.7, clangDelta: -2.9, note: 'Size optimization collapses loop headers' },
  ];

  const ablationColumns: ColumnDef<AblationRow>[] = [
    {
      key: 'name',
      label: 'Feature Subset',
      width: 170,
      isSticky: true,
      render: (val: string) => <span className="font-bold text-text-primary">{val}</span>,
    },
    {
      key: 'f1_bar',
      label: 'Inline F1 Bar',
      width: 140,
      render: (_: any, row: AblationRow) => (
        <div className="w-28 bg-bg-raised border border-border-default h-2.5 rounded-[2px] overflow-hidden">
          <div className="bg-accent h-full" style={{ width: `${row.f1 * 100}%` }} />
        </div>
      ),
    },
    {
      key: 'f1',
      label: 'Macro F1',
      width: 100,
      align: 'right',
      isMono: true,
      render: (val: number) => (
        <span className="font-bold text-accent tabular-nums">{formatPercent(val)}</span>
      ),
    },
    {
      key: 'latency',
      label: 'Latency',
      width: 90,
      align: 'right',
      isMono: true,
      render: (val: number) => `${val} ms`,
    },
  ];

  const deltaColumns: ColumnDef<DegradationDeltaRow>[] = [
    {
      key: 'opt',
      label: 'Transition',
      width: 110,
      isSticky: true,
      render: (val: string) => <span className="font-bold text-text-primary">{val}</span>,
    },
    {
      key: 'gccDelta',
      label: 'GCC Delta',
      width: 100,
      align: 'right',
      isMono: true,
      render: (val: number) => <span className="text-status-warning tabular-nums">{val}%</span>,
    },
    {
      key: 'clangDelta',
      label: 'Clang Delta',
      width: 100,
      align: 'right',
      isMono: true,
      render: (val: number) => <span className="text-status-warning tabular-nums">{val}%</span>,
    },
    {
      key: 'note',
      label: 'Structural Cause',
      width: 220,
      render: (val: string) => <span className="text-text-secondary truncate">{val}</span>,
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-default pb-3">
        <div>
          <h1 className="text-[18px] font-bold uppercase tracking-tight text-text-primary">
            Feature Ablation & Compiler Robustness
          </h1>
          <span className="text-[12px] text-text-secondary">
            Paper Table VI & Section IV-F: 4 feature groups ablation and degradation curves across O0..Os
          </span>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-3.5 py-2 bg-bg-surface border border-border-default rounded-[4px] text-[12px] text-text-primary hover:border-accent transition flex items-center gap-1.5 cursor-pointer min-h-[44px]"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} strokeWidth={1.5} />
          <span>{refreshing ? 'Re-evaluating...' : 'Re-run Evaluation'}</span>
        </button>
      </div>

      {/* Grid: Left 6 Columns Ablation Table with Inline Bars vs Right 6 Columns Degradation Line Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Table VI: Feature Ablation Study with Inline Bars */}
        <div className="lg:col-span-6 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Paper Table VI: Feature Ablation
              </span>
              <span className="text-accent font-semibold text-[12px]">Macro F1</span>
            </div>

            <DataTable
              columns={ablationColumns}
              data={ablationRows}
              idKey="name"
            />
          </div>

          <p className="p-3 text-[12px] text-text-secondary bg-bg-raised border border-border-default rounded-[4px] font-sans leading-relaxed">
            <strong>Key Finding:</strong> Adding DFG def-use chains and table lookup invariants raises F1 from 0.885 to 0.946, while full combination delivers 0.964 F1 with only 2.2 ms inference overhead.
          </p>
        </div>

        {/* Compiler Optimization Degradation Curves */}
        <div className="lg:col-span-6 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Optimization Degradation Curves (O0 → Os)
              </span>
              <div className="flex items-center gap-3 text-[12px]">
                <span className="text-status-info">• GCC</span>
                <span className="text-accent">• Clang</span>
              </div>
            </div>

            <div className="h-56 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={degradationCurves}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" opacity={0.6} />
                  <XAxis 
                    dataKey="opt" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontFamily: 'monospace' }} 
                    stroke="var(--border-default)"
                  />
                  <YAxis 
                    domain={[0.9, 1.0]} 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontFamily: 'monospace' }} 
                    stroke="var(--border-default)"
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--bg-surface)', 
                      border: '1px solid var(--border-default)', 
                      borderRadius: '4px', 
                      fontSize: '12px', 
                      fontFamily: 'monospace' 
                    }} 
                  />
                  <Line type="monotone" dataKey="gcc" stroke="var(--status-info)" strokeWidth={2} dot={{ r: 3, fill: 'var(--status-info)' }} />
                  <Line type="monotone" dataKey="clang" stroke="var(--accent)" strokeWidth={2} dot={{ r: 3, fill: 'var(--accent)' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Degradation Delta Table */}
          <div className="space-y-1">
            <span className="text-[12px] font-mono uppercase text-text-disabled block">Inter-Level Degradation Deltas</span>
            <DataTable
              columns={deltaColumns}
              data={degradationDeltas}
              idKey="opt"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
