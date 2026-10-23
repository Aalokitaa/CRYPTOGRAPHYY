import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  GitCompare, 
  Download 
} from 'lucide-react';
import { fetchRuns } from '@/lib/api';
import { formatPercent } from '@/lib/utils';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';

interface RunItem {
  id: string;
  model_type: string;
  dataset_version: string;
  overall_f1: number;
}

export const ExperimentHistoryPage: React.FC = () => {
  const { data: runsData } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
  });

  const [selectedRunA, setSelectedRunA] = useState<string>('run_transformer_01');
  const [selectedRunB, setSelectedRunB] = useState<string>('run_xgboost_02');
  const [modelFilter, setModelFilter] = useState('ALL');

  const runs: RunItem[] = (runsData?.runs || []).filter((r: any) => 
    modelFilter === 'ALL' || r.model_type.toLowerCase() === modelFilter.toLowerCase()
  );

  const runA = (runsData?.runs || []).find((r: any) => r.id === selectedRunA);
  const runB = (runsData?.runs || []).find((r: any) => r.id === selectedRunB);

  const exportRunsJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(runsData?.runs || [], null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', 'cryptoscope_experiment_runs.json');
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const columns: ColumnDef<RunItem>[] = [
    {
      key: 'id',
      label: 'Run Identifier',
      width: 170,
      isSticky: true,
      render: (val: string) => <span className="font-bold text-accent">{val}</span>,
    },
    {
      key: 'model_type',
      label: 'Model Architecture',
      width: 160,
      render: (val: string) => <span className="uppercase font-semibold text-text-primary">{val}</span>,
    },
    {
      key: 'dataset_version',
      label: 'Dataset',
      width: 110,
      isMono: true,
      render: (val: string) => <span className="text-text-secondary">{val}</span>,
    },
    {
      key: 'overall_f1',
      label: 'Macro F1',
      width: 110,
      align: 'right',
      isMono: true,
      render: (val: number) => (
        <span className="font-bold text-text-primary tabular-nums">{formatPercent(val)}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      width: 120,
      render: () => (
        <span className="px-2 py-0.5 rounded-[4px] bg-status-success/15 border border-status-success/30 text-status-success text-[12px] font-bold">
          Completed
        </span>
      ),
    },
    {
      key: 'action',
      label: 'Diff Action',
      width: 110,
      align: 'right',
      render: (_: any, r: RunItem) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedRunA(r.id);
          }}
          className="px-2.5 py-1 rounded-[4px] bg-bg-raised border border-border-default text-[12px] hover:border-accent hover:text-accent transition cursor-pointer min-h-[32px]"
        >
          Compare
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-default pb-3">
        <div>
          <h1 className="text-[18px] font-bold uppercase tracking-tight text-text-primary">
            Experiment History & Checkpoint Diffs
          </h1>
          <span className="text-[12px] text-text-secondary">
            Reproducibility log: hyperparameters, dataset versions, weights paths, and side-by-side metric deltas
          </span>
        </div>

        <button
          onClick={exportRunsJson}
          className="px-3.5 py-2 bg-bg-surface border border-border-default rounded-[4px] text-[12px] text-text-primary hover:border-accent transition flex items-center gap-1.5 cursor-pointer min-h-[44px]"
        >
          <Download className="w-4 h-4" strokeWidth={1.5} />
          <span>Export Runs (JSON)</span>
        </button>
      </div>

      {/* Side-by-Side Run Diff View (Container 1) */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border-default pb-2">
          <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-accent" strokeWidth={1.5} />
            <span>Side-by-Side Run Differential</span>
          </span>
          <span className="text-[12px] text-text-disabled">Select two runs to compare configurations</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5 text-[12px]">
            <label className="text-text-secondary text-[12px] uppercase block">Baseline (Run A)</label>
            <select
              value={selectedRunA}
              onChange={(e) => setSelectedRunA(e.target.value)}
              className="w-full bg-bg-raised border border-border-default text-text-primary rounded-[4px] px-3 py-2 text-[12px] outline-none focus:border-accent min-h-[44px]"
            >
              {(runsData?.runs || []).map((r: any) => (
                <option key={r.id} value={r.id}>
                  {r.id} • {r.model_type.toUpperCase()} ({formatPercent(r.overall_f1)})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5 text-[12px]">
            <label className="text-text-secondary text-[12px] uppercase block">Comparison (Run B)</label>
            <select
              value={selectedRunB}
              onChange={(e) => setSelectedRunB(e.target.value)}
              className="w-full bg-bg-raised border border-border-default text-text-primary rounded-[4px] px-3 py-2 text-[12px] outline-none focus:border-accent min-h-[44px]"
            >
              {(runsData?.runs || []).map((r: any) => (
                <option key={r.id} value={r.id}>
                  {r.id} • {r.model_type.toUpperCase()} ({formatPercent(r.overall_f1)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Diff Table */}
        {runA && runB && (
          <div className="border border-border-default rounded-[4px] overflow-hidden mt-3">
            <table className="w-full text-left text-[12px] table-dense">
              <thead>
                <tr className="border-b border-border-default bg-bg-raised text-text-secondary uppercase text-[12px]">
                  <th className="px-3 font-medium">Metric / Config Field</th>
                  <th className="px-3 font-medium">Run A ({runA.id})</th>
                  <th className="px-3 font-medium">Run B ({runB.id})</th>
                  <th className="px-3 font-medium text-right">Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-default text-[12px]">
                <tr className="hover:bg-bg-raised/50">
                  <td className="px-3 text-text-secondary">Model Architecture</td>
                  <td className="px-3 font-bold text-text-primary uppercase">{runA.model_type}</td>
                  <td className="px-3 font-bold text-text-primary uppercase">{runB.model_type}</td>
                  <td className="px-3 text-right text-text-disabled">—</td>
                </tr>
                <tr className="hover:bg-bg-raised/50">
                  <td className="px-3 text-text-secondary">Dataset Version</td>
                  <td className="px-3 text-text-primary">{runA.dataset_version}</td>
                  <td className="px-3 text-text-primary">{runB.dataset_version}</td>
                  <td className="px-3 text-right text-text-disabled">—</td>
                </tr>
                <tr className="hover:bg-bg-raised/50">
                  <td className="px-3 text-text-secondary">Overall Macro F1</td>
                  <td className="px-3 font-bold text-accent tabular-nums">{formatPercent(runA.overall_f1)}</td>
                  <td className="px-3 font-bold text-accent tabular-nums">{formatPercent(runB.overall_f1)}</td>
                  <td className="px-3 text-right font-bold tabular-nums">
                    <span className={runB.overall_f1 >= runA.overall_f1 ? 'text-status-success' : 'text-status-danger'}>
                      {runB.overall_f1 >= runA.overall_f1 ? '+' : ''}
                      {((runB.overall_f1 - runA.overall_f1) * 100).toFixed(2)}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Runs Table (Container 2) */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1">
          <span className="text-[12px] font-mono uppercase font-bold text-text-primary tracking-wider">
            Saved Checkpoints & Manifests ({(runsData?.runs || []).length})
          </span>
          <select
            value={modelFilter}
            onChange={(e) => setModelFilter(e.target.value)}
            className="bg-bg-surface border border-border-default text-text-primary rounded-[4px] px-3 py-1.5 text-[12px] outline-none min-h-[36px]"
          >
            <option value="ALL">All Models</option>
            <option value="transformer">Transformer</option>
            <option value="xgb">XGBoost</option>
            <option value="rf">Random Forest</option>
            <option value="cnn">1D-CNN</option>
            <option value="lstm">Bi-LSTM</option>
            <option value="svm">SVM</option>
          </select>
        </div>

        <DataTable
          columns={columns}
          data={runs}
          idKey="id"
        />
      </div>
    </div>
  );
};
