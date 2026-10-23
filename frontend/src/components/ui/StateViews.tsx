import React from 'react';
import { 
  AlertCircle, 
  AlertTriangle, 
  RefreshCw, 
  ArrowRight, 
  FilterX, 
  XCircle, 
  Terminal, 
  HelpCircle, 
  WifiOff 
} from 'lucide-react';

/**
 * 1. Flat skeleton loading state (no shimmer, opaque grey blocks)
 */
export const FlatSkeleton: React.FC<{ rows?: number; className?: string }> = ({ 
  rows = 4, 
  className = '' 
}) => {
  return (
    <div className={`space-y-2 p-4 select-none ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div 
          key={i} 
          className="h-7 bg-bg-raised border border-border-default rounded-[4px]"
          style={{ width: `${100 - (i % 3) * 15}%` }}
        />
      ))}
    </div>
  );
};

/**
 * 2. Empty state with a specific next action
 */
export const EmptyState: React.FC<{
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}> = ({ title, description, actionText, onAction, className = '' }) => {
  return (
    <div className={`p-8 text-center border border-dashed border-border-default rounded-[6px] bg-bg-surface ${className}`}>
      <span className="font-mono text-[12px] font-semibold text-text-primary block mb-1">
        {title}
      </span>
      <p className="text-[12px] text-text-secondary max-w-md mx-auto mb-4 leading-relaxed">
        {description}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-accent text-accent-on font-semibold rounded-[4px] text-[12px] transition hover:bg-accent-hover min-h-[44px] cursor-pointer"
        >
          <span>{actionText}</span>
          <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
        </button>
      )}
    </div>
  );
};

/**
 * 3. Technical error state with retry and detail
 */
export const ErrorState: React.FC<{
  title?: string;
  errorDetail?: string;
  onRetry?: () => void;
  className?: string;
}> = ({
  title = 'Analysis / Request Failed',
  errorDetail = 'An internal execution error occurred while processing binary structures.',
  onRetry,
  className = ''
}) => {
  return (
    <div className={`p-4 border border-status-danger/40 bg-status-danger/10 text-status-danger rounded-[6px] space-y-2 text-[12px] ${className}`}>
      <div className="flex items-center gap-2 font-semibold">
        <AlertCircle className="w-4 h-4 shrink-0" strokeWidth={1.5} />
        <span>{title}</span>
      </div>
      <div className="font-mono text-[12px] bg-bg-base/80 p-2 rounded-[4px] border border-status-danger/30 text-text-primary select-all">
        {errorDetail}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-status-danger text-white font-semibold rounded-[4px] text-[12px] transition hover:opacity-90 min-h-[44px] cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
          <span>Retry Operation</span>
        </button>
      )}
    </div>
  );
};

/**
 * 4. Filtered-to-zero results state
 */
export const FilteredZeroState: React.FC<{
  activeFiltersCount?: number;
  onResetFilters: () => void;
  className?: string;
}> = ({ activeFiltersCount = 1, onResetFilters, className = '' }) => {
  return (
    <div className={`p-8 text-center border border-border-default rounded-[6px] bg-bg-surface ${className}`}>
      <FilterX className="w-8 h-8 mx-auto mb-2 text-text-disabled" strokeWidth={1.5} />
      <span className="font-mono text-[12px] font-semibold text-text-primary block mb-1">
        No Matching Functions or Binaries Found
      </span>
      <p className="text-[12px] text-text-secondary max-w-sm mx-auto mb-4 leading-relaxed">
        {activeFiltersCount} active filter criteria returned 0 records. Adjust your query or confidence threshold.
      </p>
      <button
        onClick={onResetFilters}
        className="inline-flex items-center gap-1.5 px-3 py-2 border border-border-default bg-bg-raised text-text-primary font-mono text-[12px] rounded-[4px] hover:border-accent min-h-[44px] cursor-pointer"
      >
        <span>Reset Active Filters</span>
      </button>
    </div>
  );
};

/**
 * 5. Failed Job state
 */
export const FailedJobState: React.FC<{
  jobId: string;
  stepName?: string;
  errorMessage?: string;
  onRestart?: () => void;
  className?: string;
}> = ({ jobId, stepName = 'Feature Extraction', errorMessage = 'Process terminated with non-zero exit code.', onRestart, className = '' }) => {
  return (
    <div className={`p-4 border border-status-danger/40 bg-status-danger/10 text-text-primary rounded-[6px] space-y-3 text-[12px] ${className}`}>
      <div className="flex items-center gap-2 text-status-danger font-semibold">
        <XCircle className="w-4 h-4 shrink-0" strokeWidth={1.5} />
        <span>Background Task Failed: {stepName}</span>
      </div>
      <div className="font-mono text-[12px] bg-bg-base p-2.5 rounded-[4px] border border-status-danger/30 space-y-1">
        <div className="text-text-disabled">Job ID: {jobId}</div>
        <div className="text-status-danger">{errorMessage}</div>
      </div>
      {onRestart && (
        <button
          onClick={onRestart}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-status-danger text-white font-mono text-[12px] rounded-[4px] hover:opacity-90 min-h-[44px] cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
          <span>Restart Job</span>
        </button>
      )}
    </div>
  );
};

/**
 * 6. Missing Toolchain state
 */
export const MissingToolchainState: React.FC<{
  missingIsa: string;
  suggestedPackage?: string;
  installCommand?: string;
  className?: string;
}> = ({
  missingIsa,
  suggestedPackage = 'gcc-arm-linux-gnueabi',
  installCommand = 'apt install -y gcc-arm-linux-gnueabi g++-arm-linux-gnueabi',
  className = ''
}) => {
  return (
    <div className={`p-4 border border-status-warning/40 bg-status-warning/10 text-text-primary rounded-[6px] space-y-2 text-[12px] ${className}`}>
      <div className="flex items-center gap-2 text-status-warning font-semibold">
        <Terminal className="w-4 h-4 shrink-0" strokeWidth={1.5} />
        <span>Missing Cross-Compiler Toolchain: {missingIsa}</span>
      </div>
      <p className="text-[12px] text-text-secondary leading-relaxed">
        The toolchain for compiling target architecture {missingIsa} was not detected on the host. Synthetic binary fallback will be used until the compiler package is installed.
      </p>
      <div className="font-mono text-[12px] bg-bg-base p-2 rounded-[4px] border border-border-default text-accent select-all flex items-center justify-between">
        <code>{installCommand}</code>
        <span className="text-text-disabled text-[12px]">bash</span>
      </div>
    </div>
  );
};

/**
 * 7. Low-Confidence / Unknown Prediction warning
 */
export const LowConfidenceWarning: React.FC<{
  confidence: number;
  threshold?: number;
  suggestedPrimitive?: string;
  onManualOverride?: () => void;
  className?: string;
}> = ({ confidence, threshold = 0.5, suggestedPrimitive = 'UNKNOWN', onManualOverride, className = '' }) => {
  return (
    <div className={`p-3 border border-status-warning/40 bg-status-warning/10 rounded-[6px] flex items-start gap-2.5 text-[12px] ${className}`}>
      <HelpCircle className="w-4 h-4 text-status-warning shrink-0 mt-0.5" strokeWidth={1.5} />
      <div className="flex-1 space-y-1">
        <span className="font-semibold text-status-warning font-mono block">
          Low Confidence Prediction ({Math.round(confidence * 100)}% &lt; {Math.round(threshold * 100)}% threshold)
        </span>
        <p className="text-[12px] text-text-secondary leading-relaxed">
          The hierarchical model did not meet the confidence threshold for {suggestedPrimitive}. Classified as Non-Crypto or Ambiguous Primitive.
        </p>
        {onManualOverride && (
          <button
            onClick={onManualOverride}
            className="text-[12px] font-mono text-accent underline hover:opacity-80 cursor-pointer min-h-[44px] flex items-center"
          >
            Manually annotate ground-truth label →
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * 8. Offline Backend state
 */
export const OfflineBackendState: React.FC<{
  onRetryConnection?: () => void;
  className?: string;
}> = ({ onRetryConnection, className = '' }) => {
  return (
    <div className={`p-8 text-center border border-status-danger/40 bg-bg-surface rounded-[6px] space-y-3 ${className}`}>
      <WifiOff className="w-8 h-8 mx-auto text-status-danger" strokeWidth={1.5} />
      <span className="font-mono text-[14px] font-bold text-text-primary block">
        FastAPI Backend Offline or Unreachable
      </span>
      <p className="text-[12px] text-text-secondary max-w-md mx-auto leading-relaxed">
        Could not connect to the CryptoScope core analysis service at <code>http://127.0.0.1:8000</code>. Verify that the Uvicorn server is running.
      </p>
      <div className="inline-block font-mono text-[12px] bg-bg-raised p-2 rounded-[4px] border border-border-default text-text-primary text-left">
        <code>uvicorn backend.app.main:app --host 127.0.0.1 --port 8000</code>
      </div>
      {onRetryConnection && (
        <div className="pt-2">
          <button
            onClick={onRetryConnection}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-accent text-accent-on font-mono text-[12px] font-medium rounded-[4px] hover:bg-accent-hover min-h-[44px] cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * 9. Unsupported ISA Warning banner (e.g. Xtensa, AVR, etc.)
 */
export const UnsupportedIsaWarning: React.FC<{
  isa: string;
  targetFile?: string;
  onGhidraFallback?: () => void;
}> = ({ isa, targetFile, onGhidraFallback }) => {
  return (
    <div className="p-3.5 border border-status-warning/40 bg-status-warning/10 text-text-primary rounded-[6px] flex items-start gap-3 text-[12px]">
      <AlertTriangle className="w-4 h-4 text-status-warning shrink-0 mt-0.5" strokeWidth={1.5} />
      <div className="space-y-1 flex-1">
        <span className="font-semibold text-status-warning block font-mono">
          Unsupported / Non-Standard Architecture: {isa}
        </span>
        <p className="text-[12px] text-text-secondary leading-relaxed">
          The binary {targetFile ? <code className="text-accent">{targetFile}</code> : 'target'} targets {isa}, which lacks native Capstone disassembler coverage. Analysis fell back to trial heuristics and byte-level entropy scanning.
        </p>
        {onGhidraFallback && (
          <button
            onClick={onGhidraFallback}
            className="mt-1 text-[12px] font-mono text-accent underline hover:opacity-80 min-h-[44px] flex items-center cursor-pointer"
          >
            Switch to Ghidra Headless backend for {isa} recovery →
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * 10. Mandatory Scientific Caveat Banner
 */
export const ScientificCaveatBanner: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`p-3 border border-status-warning/30 bg-status-warning/10 rounded-[6px] flex items-start gap-2.5 text-[12px] ${className}`}>
      <AlertTriangle className="w-4 h-4 text-status-warning shrink-0 mt-0.5" strokeWidth={1.5} />
      <div>
        <span className="font-semibold text-status-warning font-mono uppercase text-[12px] tracking-wider block">
          Static Analysis Limitation Notice
        </span>
        <p className="text-[12px] text-text-secondary leading-relaxed mt-0.5">
          Static binary analysis identifies candidate cryptographic primitives and inter-call relationships. As established in paper Section V-F, static data alone cannot definitively prove runtime protocol state or handshake completion.
        </p>
      </div>
    </div>
  );
};
