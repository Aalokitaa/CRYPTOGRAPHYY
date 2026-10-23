import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Play, 
  Square, 
  Terminal 
} from 'lucide-react';
import { triggerTraining, fetchJobStatus, fetchDatasets, fetchRuns } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export const TrainingConsolePage: React.FC = () => {
  const { setActiveJobId } = useAppStore();

  const [level, setLevel] = useState<number>(3);
  const [selectedModels, setSelectedModels] = useState<string[]>(['rf', 'transformer']);
  const [datasetVersion, setDatasetVersion] = useState('v1.0.0');
  const [searchBudget, setSearchBudget] = useState(25);
  const [randomSeed, setRandomSeed] = useState(42);

  // 4 Feature Toggles
  const [enableByte, setEnableByte] = useState(true);
  const [enableInstruction, setEnableInstruction] = useState(true);
  const [enableCfg, setEnableCfg] = useState(true);
  const [enableDfg, setEnableDfg] = useState(true);
  const [useSemanticTokens, setUseSemanticTokens] = useState(true);

  const [isTraining, setIsTraining] = useState(false);
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState('Idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [completedRunId, setCompletedRunId] = useState<string | null>(null);

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: fetchDatasets,
  });

  const { data: runs, refetch: refetchRuns } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
  });

  // Simulated live loss & metric curves
  const liveLossData = [
    { epoch: 1, trainLoss: 1.42, valLoss: 1.48, valF1: 0.62 },
    { epoch: 5, trainLoss: 0.88, valLoss: 0.94, valF1: 0.78 },
    { epoch: 10, trainLoss: 0.52, valLoss: 0.61, valF1: 0.86 },
    { epoch: 15, trainLoss: 0.31, valLoss: 0.42, valF1: 0.91 },
    { epoch: 20, trainLoss: 0.18, valLoss: 0.28, valF1: 0.94 },
    { epoch: 25, trainLoss: 0.09, valLoss: 0.21, valF1: 0.955 },
  ];

  const handleStartTraining = async () => {
    setIsTraining(true);
    setProgress(5);
    setStep('Initializing zero-leakage split');
    setLogs(['[ML Engine] Partitioning dataset into 70/15/15 grouped splits (source_program + implementation)...']);

    try {
      const res = await triggerTraining({
        model_type: selectedModels[0] || 'rf',
        level: level,
        dataset_version: datasetVersion,
        enable_byte: enableByte,
        enable_instruction: enableInstruction,
        enable_cfg: enableCfg,
        enable_dfg: enableDfg,
        use_semantic_tokens: useSemanticTokens,
      });

      setActiveJobId(res.job_id);

      const interval = setInterval(async () => {
        try {
          const job = await fetchJobStatus(res.job_id);
          setProgress(job.progress);
          setStep(job.step);
          if (job.logs && job.logs.length > 0) {
            setLogs(job.logs);
          }

          if (job.status === 'completed' && job.result_id) {
            setCompletedRunId(job.result_id);
            setIsTraining(false);
            setActiveJobId(null);
            clearInterval(interval);
            refetchRuns();
          } else if (job.status === 'failed') {
            setIsTraining(false);
            setActiveJobId(null);
            clearInterval(interval);
          }
        } catch {
          // retry
        }
      }, 1000);
    } catch {
      setIsTraining(false);
    }
  };

  const toggleModel = (m: string) => {
    if (selectedModels.includes(m)) {
      if (selectedModels.length > 1) setSelectedModels(selectedModels.filter(x => x !== m));
    } else {
      setSelectedModels([...selectedModels, m]);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Title */}
      <div className="border-b border-border-default pb-3 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-[18px] font-bold uppercase tracking-tight text-text-primary">
            Hierarchical Model Training Console
          </h1>
          <span className="text-[12px] text-text-secondary">
            Paper Section III-E: Zero-leakage grouped splitting, hyperparameter search, and PyTorch deep models
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isTraining ? (
            <button
              onClick={() => setIsTraining(false)}
              className="px-4 py-2 bg-status-danger text-white font-bold rounded-[4px] text-[12px] flex items-center gap-1.5 cursor-pointer min-h-[44px]"
            >
              <Square className="w-4 h-4 fill-current" strokeWidth={1.5} />
              <span>Stop Training</span>
            </button>
          ) : (
            <button
              onClick={handleStartTraining}
              className="px-4 py-2 bg-accent text-accent-on font-bold rounded-[4px] text-[12px] hover:bg-accent-hover transition flex items-center gap-1.5 cursor-pointer min-h-[44px]"
            >
              <Play className="w-4 h-4 fill-current" strokeWidth={1.5} />
              <span>Launch Run</span>
            </button>
          )}
        </div>
      </div>

      {/* Grid: Left 5 Columns Config vs Right 7 Columns Live Curves & Logs (Max 2 Containers) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 Cols: Config Form Container */}
        <div className="lg:col-span-5 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
          <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
            Training Parameters
          </span>

          {/* Level Segmented Control */}
          <div className="space-y-1.5">
            <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Target Hierarchy Level</label>
            <div className="grid grid-cols-3 gap-1 bg-bg-raised p-1 rounded-[4px] border border-border-default">
              {[
                { val: 1, label: 'L1: Crypto' },
                { val: 2, label: 'L2: Family' },
                { val: 3, label: 'L3: Primitive' },
              ].map((lvl) => (
                <button
                  key={lvl.val}
                  onClick={() => setLevel(lvl.val)}
                  className={`py-2 text-[12px] rounded-[2px] transition cursor-pointer min-h-[36px] ${
                    level === lvl.val
                      ? 'bg-bg-surface text-accent font-bold border border-border-default'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {lvl.label}
                </button>
              ))}
            </div>
          </div>

          {/* Models Multi-Select */}
          <div className="space-y-1.5">
            <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Model Architectures</label>
            <div className="grid grid-cols-2 gap-2 text-[12px]">
              {[
                { id: 'rf', label: 'Random Forest' },
                { id: 'xgb', label: 'XGBoost' },
                { id: 'svm', label: 'SVM (RBF)' },
                { id: 'cnn', label: '1D-CNN' },
                { id: 'lstm', label: 'Bi-LSTM' },
                { id: 'transformer', label: 'Transformer' },
              ].map(m => (
                <label key={m.id} className="flex items-center gap-2 p-2 rounded-[4px] bg-bg-raised border border-border-default cursor-pointer min-h-[36px]">
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(m.id)}
                    onChange={() => toggleModel(m.id)}
                    className="accent-accent w-4 h-4"
                  />
                  <span className="text-text-primary truncate">{m.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Proportional Split Bar (70 / 15 / 15) */}
          <div className="space-y-2 pt-2 border-t border-border-default">
            <div className="flex justify-between text-[12px] text-text-secondary">
              <span>Grouped Dataset Split:</span>
              <span className="text-text-primary font-bold">70% Train / 15% Val / 15% Test</span>
            </div>
            <div className="h-5 w-full bg-bg-raised rounded-[2px] border border-border-default flex overflow-hidden text-[12px] font-bold text-center leading-5 select-none">
              <div className="w-[70%] bg-accent text-accent-on border-r border-border-default">70% Train</div>
              <div className="w-[15%] bg-status-info text-white border-r border-border-default">15% Val</div>
              <div className="w-[15%] bg-status-success text-white">15% Test</div>
            </div>
            <p className="text-[12px] text-text-secondary leading-relaxed font-sans">
              *Grouped by source program + implementation. No function across compiles is ever split between Train and Test (Zero Leakage).
            </p>
          </div>

          {/* Search Budget & Seed */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border-default">
            <div className="space-y-1.5">
              <label className="text-text-secondary text-[12px] block">Optuna Trials: {searchBudget}</label>
              <input type="range" min="10" max="100" step="5" value={searchBudget} onChange={e => setSearchBudget(parseInt(e.target.value))} className="w-full accent-accent h-2 cursor-pointer" />
            </div>
            <div className="space-y-1.5">
              <label className="text-text-secondary text-[12px] block">Random Seed</label>
              <input type="number" value={randomSeed} onChange={e => setRandomSeed(parseInt(e.target.value))} className="w-full bg-bg-raised border border-border-default rounded-[4px] px-3 py-1.5 text-[12px] text-text-primary outline-none focus:border-accent min-h-[36px]" />
            </div>
          </div>
        </div>

        {/* Right 7 Cols: Live Curves & Logs Container */}
        <div className="lg:col-span-7 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
          {/* Live Metric & Loss Curves Chart */}
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Training Loss & Validation F1 Trajectory
              </span>
              <div className="flex items-center gap-3 text-[12px]">
                <span className="text-accent">• Val Macro F1</span>
                <span className="text-status-danger">• Train Loss</span>
              </div>
            </div>

            <div className="h-56 w-full pt-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={liveLossData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" opacity={0.6} />
                  <XAxis 
                    dataKey="epoch" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontFamily: 'monospace' }} 
                    unit=" ep" 
                    stroke="var(--border-default)"
                  />
                  <YAxis 
                    domain={[0, 1.6]} 
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
                  <Line type="monotone" dataKey="valF1" stroke="var(--accent)" strokeWidth={2} dot={{ r: 2, fill: 'var(--accent)' }} />
                  <Line type="monotone" dataKey="trainLoss" stroke="var(--status-danger)" strokeWidth={1.5} dot={{ r: 2, fill: 'var(--status-danger)' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Training Log Console */}
          <div className="border border-border-default bg-bg-base rounded-[4px] p-3 text-[12px] flex flex-col h-56 font-mono">
            <div className="flex items-center justify-between border-b border-border-default/60 pb-1.5 mb-2">
              <div className="flex items-center gap-2 text-text-primary">
                <Terminal className="w-4 h-4 text-accent" strokeWidth={1.5} />
                <span className="text-[12px] font-semibold uppercase tracking-wider">Trainer Runtime Stream</span>
              </div>
              <span className="text-[12px] text-text-disabled">Epoch Progress</span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-1 select-text">
              {logs.length === 0 ? (
                <div className="text-text-disabled italic pt-2">Click 'Launch Run' to start model training and stream telemetry.</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="leading-relaxed">
                    <span className="text-text-disabled mr-2">&gt;</span>
                    <span className={log.includes('complete') ? 'text-status-success' : 'text-text-primary'}>{log}</span>
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
