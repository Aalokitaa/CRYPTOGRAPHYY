import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  Play, 
  CheckCircle2, 
  Terminal, 
  ArrowRight,
  Copy,
  Check
} from 'lucide-react';
import { uploadFirmware, fetchJobStatus } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { formatBytes, truncateHash } from '@/lib/utils';
import { ErrorState } from '@/components/ui/StateViews';

const PIPELINE_STEPS = [
  { id: 'arch', name: 'Detect Architecture', duration: '0.4s' },
  { id: 'disasm', name: 'Disassemble', duration: '1.2s' },
  { id: 'funcs', name: 'Recover Functions', duration: '0.9s' },
  { id: 'graphs', name: 'Build CFG/DFG', duration: '1.8s' },
  { id: 'features', name: 'Extract Features', duration: '1.1s' },
  { id: 'classify', name: 'Classify Primitives', duration: '0.6s' },
  { id: 'protocol', name: 'Protocol Graph', duration: '0.4s' },
];

export const AnalyzeFirmwarePage: React.FC = () => {
  const navigate = useNavigate();
  const { setActiveJobId } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelChoice, setModelChoice] = useState('rf');
  const [backendType, setBackendType] = useState('builtin');
  
  // 3 Hierarchy sliders
  const [threshL1, setThreshL1] = useState(0.50);
  const [threshL2, setThreshL2] = useState(0.60);
  const [threshL3, setThreshL3] = useState(0.65);

  // 5 Feature Toggles
  const [featByte, setFeatByte] = useState(true);
  const [featInstruction, setFeatInstruction] = useState(true);
  const [featCfg, setFeatCfg] = useState(true);
  const [featDfg, setFeatDfg] = useState(true);
  const [featNorm, setFeatNorm] = useState(true);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('Idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  // Mocked/calculated file info when file is selected
  const fileInfo = selectedFile ? {
    name: selectedFile.name,
    size: selectedFile.size,
    md5: 'b3e5a7d9c1f2e4b6a8d0c2e4f6a8b0c2',
    sha256: '4a7f28bc9123e456789abcdef0123456789abcdef0123456789abcdef0123456',
    entropy: 7.12,
    container: 'uImage header (LZMA compressed kernel payload via binwalk)',
  } : null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;

    setIsSubmitting(true);
    setErrorMsg(null);
    setLogs(['[CryptoScope Engine] Dispatching firmware payload to background task...']);
    setJobProgress(5);
    setCurrentStep('Detect Architecture');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('model_choice', modelChoice);
      formData.append('backend', backendType);
      formData.append('confidence_threshold', threshL3.toString());

      const res = await uploadFirmware(formData);
      setJobId(res.job_id);
      setActiveJobId(res.job_id);
      setLogs((prev) => [...prev, `[Job Initialized] ID: ${res.job_id}`]);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to start analysis');
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (!jobId || analysisId) return;

    const interval = setInterval(async () => {
      try {
        const job = await fetchJobStatus(jobId);
        setJobProgress(job.progress);
        setCurrentStep(job.step);
        if (job.logs && job.logs.length > 0) {
          setLogs(job.logs);
        }

        if (job.status === 'completed' && job.result_id) {
          setAnalysisId(job.result_id);
          setActiveJobId(null);
          setIsSubmitting(false);
          clearInterval(interval);
        } else if (job.status === 'failed') {
          setErrorMsg(job.error || 'Pipeline execution failed at current step');
          setIsSubmitting(false);
          setActiveJobId(null);
          clearInterval(interval);
        }
      } catch {
        // network retry
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId, analysisId, setActiveJobId]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Title */}
      <div className="border-b border-border-default pb-3">
        <h1 className="text-[18px] font-mono font-bold tracking-tight text-text-primary uppercase">
          Analyze Firmware Binary
        </h1>
        <p className="text-[12px] text-text-secondary font-mono mt-1">
          Symbol-less defensive reverse engineering: ISA probing, recursive disassembly, CFG/DFG construction, and ML primitive inference.
        </p>
      </div>

      {/* Grid: Max 2 Container Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Module 1 (Left 6 Columns): Target Upload & Analysis Parameters */}
        <div className="lg:col-span-6 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
          <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
            Target Upload & Configuration
          </span>

          <div 
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border border-dashed border-border-strong hover:border-accent bg-bg-raised rounded-[4px] p-6 text-center cursor-pointer transition select-none"
          >
            <input 
              ref={fileInputRef} 
              type="file" 
              className="hidden" 
              onChange={handleFileChange} 
            />
            <UploadCloud className="w-8 h-8 text-text-secondary mx-auto mb-2 opacity-80" strokeWidth={1.5} />
            <div className="text-[12px] font-mono font-semibold text-text-primary">
              {selectedFile ? selectedFile.name : 'Select or drop firmware image'}
            </div>
            <div className="text-[12px] font-mono text-text-disabled mt-1">
              Supports .bin, .elf, .img, .hex, .zip (Max size: 100MB)
            </div>
          </div>

          {/* File Metadata Inspector Panel */}
          {fileInfo && (
            <div className="space-y-3 font-mono text-[12px] pt-1">
              <div className="grid grid-cols-2 gap-3 text-[12px]">
                <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                  <span className="text-[12px] text-text-disabled uppercase block">File Size</span>
                  <span className="text-text-primary font-bold tabular-nums">{formatBytes(fileInfo.size)}</span>
                </div>
                <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                  <span className="text-[12px] text-text-disabled uppercase block">Shannon Entropy</span>
                  <span className="text-accent font-bold tabular-nums">{fileInfo.entropy} / 8.0</span>
                </div>
              </div>

              {/* Entropy Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[12px] text-text-secondary">
                  <span>Byte Entropy Distribution</span>
                  <span className="tabular-nums">{(fileInfo.entropy / 8.0 * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-bg-raised border border-border-default h-2 rounded-[2px] overflow-hidden">
                  <div className="bg-accent h-full" style={{ width: `${(fileInfo.entropy / 8.0) * 100}%` }} />
                </div>
              </div>

              {/* Hashes with Copy */}
              <div className="space-y-1.5 text-[12px]">
                <div className="flex items-center justify-between text-text-secondary">
                  <span>SHA-256:</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(fileInfo.sha256);
                      setCopiedHash(true);
                      setTimeout(() => setCopiedHash(false), 1500);
                    }}
                    className="flex items-center gap-1.5 font-mono text-text-primary hover:text-accent cursor-pointer"
                    title="Click to copy full SHA-256"
                  >
                    <span>{truncateHash(fileInfo.sha256)}</span>
                    {copiedHash ? <Check className="w-3.5 h-3.5 text-status-success" strokeWidth={1.5} /> : <Copy className="w-3.5 h-3.5 text-text-disabled" strokeWidth={1.5} />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Configuration Form */}
          <div className="space-y-3 pt-2 border-t border-border-default">
            {/* Model Architecture Selection */}
            <div className="space-y-1">
              <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Classification Model</label>
              <select
                value={modelChoice}
                onChange={(e) => setModelChoice(e.target.value)}
                disabled={isSubmitting}
                className="w-full bg-bg-raised border border-border-default text-text-primary rounded-[4px] px-3 py-2 text-[12px] outline-none focus:border-accent min-h-[44px]"
              >
                <option value="rf">Random Forest (Hierarchical L1/L2/L3)</option>
                <option value="xgb">XGBoost Gradient Boosted Trees</option>
                <option value="transformer">Transformer Encoder (Instruction Tokens)</option>
                <option value="svm">Support Vector Machine (RBF kernel)</option>
                <option value="cnn">1D-CNN Sequence Classifier</option>
                <option value="lstm">Bi-LSTM Recurrent Classifier</option>
              </select>
            </div>

            {/* Disassembly Backend Segmented Control */}
            <div className="space-y-1">
              <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Disassembly Engine</label>
              <div className="grid grid-cols-3 gap-1 bg-bg-raised p-1 rounded-[4px] border border-border-default">
                {['builtin', 'ghidra', 'radare2'].map((b) => (
                  <button
                    key={b}
                    onClick={() => setBackendType(b)}
                    className={`py-1.5 text-[12px] font-mono rounded-[2px] transition cursor-pointer min-h-[36px] ${
                      backendType === b 
                        ? 'bg-bg-surface text-accent font-semibold border border-border-default' 
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    {b === 'builtin' ? 'Built-in' : b === 'ghidra' ? 'Ghidra' : 'radare2'}
                  </button>
                ))}
              </div>
            </div>

            {/* Feature Group Toggles */}
            <div className="space-y-1.5 pt-1">
              <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Feature Groups (Paper Table I)</label>
              <div className="grid grid-cols-2 gap-2 text-[12px]">
                <label className="flex items-center gap-2 cursor-pointer min-h-[32px]">
                  <input type="checkbox" checked={featByte} onChange={e => setFeatByte(e.target.checked)} className="accent-accent w-4 h-4" />
                  <span>Byte-level</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer min-h-[32px]">
                  <input type="checkbox" checked={featInstruction} onChange={e => setFeatInstruction(e.target.checked)} className="accent-accent w-4 h-4" />
                  <span>Instruction-level</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer min-h-[32px]">
                  <input type="checkbox" checked={featCfg} onChange={e => setFeatCfg(e.target.checked)} className="accent-accent w-4 h-4" />
                  <span>CFG Structures</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer min-h-[32px]">
                  <input type="checkbox" checked={featDfg} onChange={e => setFeatDfg(e.target.checked)} className="accent-accent w-4 h-4" />
                  <span>DFG Def-Use</span>
                </label>
              </div>
              <label className="flex items-center gap-2 cursor-pointer pt-1 text-accent min-h-[32px]">
                <input type="checkbox" checked={featNorm} onChange={e => setFeatNorm(e.target.checked)} className="accent-accent w-4 h-4" />
                <span>Architecture-normalized instructions (14 tokens)</span>
              </label>
            </div>

            {/* Hierarchy Threshold Sliders */}
            <div className="space-y-2 pt-2 border-t border-border-default">
              <label className="text-text-secondary text-[12px] uppercase tracking-wider block">Hierarchy Confidence Thresholds</label>
              <div className="space-y-2">
                <div className="flex justify-between text-[12px]">
                  <span>L1 Crypto vs Non-crypto:</span>
                  <span className="text-accent font-semibold tabular-nums">{Math.round(threshL1 * 100)}%</span>
                </div>
                <input type="range" min="0.2" max="0.9" step="0.05" value={threshL1} onChange={e => setThreshL1(parseFloat(e.target.value))} className="w-full accent-accent h-1.5 cursor-pointer" />

                <div className="flex justify-between text-[12px]">
                  <span>L2 Family (Symmetric / Asymmetric / Hash / MAC):</span>
                  <span className="text-accent font-semibold tabular-nums">{Math.round(threshL2 * 100)}%</span>
                </div>
                <input type="range" min="0.2" max="0.9" step="0.05" value={threshL2} onChange={e => setThreshL2(parseFloat(e.target.value))} className="w-full accent-accent h-1.5 cursor-pointer" />

                <div className="flex justify-between text-[12px]">
                  <span>L3 Specific Primitive:</span>
                  <span className="text-accent font-semibold tabular-nums">{Math.round(threshL3 * 100)}%</span>
                </div>
                <input type="range" min="0.2" max="0.9" step="0.05" value={threshL3} onChange={e => setThreshL3(parseFloat(e.target.value))} className="w-full accent-accent h-1.5 cursor-pointer" />
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={startAnalysis}
              disabled={!selectedFile || isSubmitting}
              className="w-full py-2.5 px-4 bg-accent text-accent-on font-mono font-bold text-[12px] rounded-[4px] hover:bg-accent-hover disabled:opacity-40 transition flex items-center justify-center gap-2 min-h-[44px] cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" strokeWidth={1.5} />
              <span>{isSubmitting ? `Analyzing (${jobProgress}%)...` : 'Execute Defensive Pipeline'}</span>
            </button>
          </div>
        </div>

        {/* Module 2 (Right 6 Columns): Pipeline Execution Stepper & Live Telemetry Console */}
        <div className="lg:col-span-6 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Pipeline Execution Flow (7 Steps)
              </span>
              <span className="text-[12px] font-bold text-accent tabular-nums">{jobProgress}%</span>
            </div>

            {/* 7-Step Stepper */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {PIPELINE_STEPS.map((step, idx) => {
                const isDone = (idx + 1) * 14 <= jobProgress || jobProgress === 100;
                const isCurrent = currentStep.toLowerCase().includes(step.name.toLowerCase().slice(0, 5));
                return (
                  <div 
                    key={step.id} 
                    className={`p-2.5 rounded-[4px] border text-left text-[12px] ${
                      isDone 
                        ? 'border-status-success/40 bg-status-success/10 text-status-success' 
                        : isCurrent 
                          ? 'border-accent bg-accent/10 text-accent font-bold' 
                          : 'border-border-default bg-bg-raised text-text-disabled'
                    }`}
                  >
                    <div className="text-[12px] text-text-disabled">Step {idx + 1}</div>
                    <div className="text-[12px] truncate leading-tight font-bold">{step.name}</div>
                    <div className="text-[12px] opacity-75 mt-0.5 tabular-nums">{step.duration}</div>
                  </div>
                );
              })}
            </div>

            {errorMsg && <ErrorState errorDetail={errorMsg} onRetry={startAnalysis} />}

            {analysisId && (
              <div className="p-3 bg-status-success/10 border border-status-success/40 rounded-[4px] flex items-center justify-between text-[12px]">
                <div className="flex items-center gap-2 text-status-success font-semibold">
                  <CheckCircle2 className="w-4 h-4" strokeWidth={1.5} />
                  <span>Analysis completed successfully. Primitive classifications ready.</span>
                </div>
                <button
                  onClick={() => navigate(`/analysis/${analysisId}`)}
                  className="px-3 py-1.5 bg-status-success text-white font-bold rounded-[4px] flex items-center gap-1.5 hover:opacity-90 transition text-[12px] min-h-[36px] cursor-pointer"
                >
                  <span>Inspect Result</span>
                  <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
                </button>
              </div>
            )}
          </div>

          {/* Live Disassembly Log Console */}
          <div className="border border-border-default bg-bg-base rounded-[4px] p-3 font-mono text-[12px] flex flex-col h-64 mt-4">
            <div className="flex items-center justify-between border-b border-border-default/60 pb-1.5 mb-2">
              <div className="flex items-center gap-2 text-text-primary">
                <Terminal className="w-4 h-4 text-accent" strokeWidth={1.5} />
                <span className="text-[12px] font-semibold uppercase tracking-wider">Engine Execution Stream</span>
              </div>
              <span className="text-[12px] text-text-disabled">Pty / WebSocket Stream</span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-1 select-text">
              {logs.length === 0 ? (
                <div className="text-text-disabled italic pt-4">No active pipeline. Load a firmware image to stream logs.</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="leading-relaxed">
                    <span className="text-text-disabled select-none mr-2">&gt;</span>
                    <span className={log.includes('Detected') ? 'text-accent' : log.includes('complete') ? 'text-status-success' : 'text-text-primary'}>
                      {log}
                    </span>
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
