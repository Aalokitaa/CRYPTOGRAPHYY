import React from 'react';

export interface StatItem {
  label: string;
  value: string | number;
  subtext?: string;
  highlight?: boolean;
}

interface StatStripProps {
  items: StatItem[];
  className?: string;
}

export const StatStrip: React.FC<StatStripProps> = ({ items, className = '' }) => {
  return (
    <div 
      className={`border border-border-default bg-bg-surface rounded-[6px] divide-y sm:divide-y-0 sm:divide-x divide-border-default grid grid-cols-2 sm:grid-cols-4 ${className}`}
    >
      {items.map((item, idx) => (
        <div key={idx} className="p-4 flex flex-col justify-between">
          <span className="text-[12px] font-mono uppercase tracking-[0.04em] text-text-secondary mb-1">
            {item.label}
          </span>
          <div className="flex items-baseline gap-2">
            <span 
              className={`text-[20px] leading-tight font-mono font-bold tabular-nums ${
                item.highlight ? 'text-accent' : 'text-text-primary'
              }`}
            >
              {item.value}
            </span>
          </div>
          {item.subtext && (
            <span className="text-[12px] text-text-disabled font-mono mt-0.5 truncate">
              {item.subtext}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};
