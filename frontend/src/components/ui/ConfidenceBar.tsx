import React from 'react';
import { formatPercent } from '@/lib/utils';

interface ConfidenceBarProps {
  confidence: number;
  threshold?: number; // e.g. 0.5
  className?: string;
  showText?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  confidence,
  threshold = 0.5,
  className = '',
  showText = true,
}) => {
  const percentage = Math.max(0, Math.min(100, Math.round(confidence * 100)));
  const thresholdPercent = Math.max(0, Math.min(100, Math.round(threshold * 100)));
  const isHigh = confidence >= threshold;

  return (
    <div className={`inline-flex items-center gap-2 font-mono text-[12px] ${className}`}>
      {/* 64px flat inline bar with threshold marker */}
      <div 
        className="relative w-16 h-2 bg-bg-raised border border-border-default rounded-[2px] overflow-visible"
        title={`Confidence: ${percentage}% (Threshold: ${thresholdPercent}%)`}
      >
        {/* Fill */}
        <div
          className={`h-full transition-all duration-150 ${isHigh ? 'bg-accent' : 'bg-status-danger'}`}
          style={{ width: `${percentage}%` }}
        />
        {/* Threshold Tick Marker */}
        <div
          className="absolute -top-0.5 -bottom-0.5 w-[2px] bg-border-strong z-10 pointer-events-none"
          style={{ left: `${thresholdPercent}%` }}
          title={`Threshold Marker: ${thresholdPercent}%`}
        />
      </div>

      {showText && (
        <span 
          className={`tabular-nums text-right font-medium w-11 ${
            isHigh ? 'text-text-primary' : 'text-status-warning'
          }`}
        >
          {formatPercent(confidence)}
        </span>
      )}
    </div>
  );
};
