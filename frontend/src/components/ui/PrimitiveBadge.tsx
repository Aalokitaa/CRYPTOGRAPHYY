import React from 'react';
import { getPrimitiveMeta } from '@/lib/utils';

interface PrimitiveBadgeProps {
  primitive: string;
  className?: string;
  showTagOnly?: boolean;
}

export const PrimitiveBadge: React.FC<PrimitiveBadgeProps> = ({
  primitive,
  className = '',
  showTagOnly = false,
}) => {
  const meta = getPrimitiveMeta(primitive);

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] border font-mono text-[12px] font-medium leading-none select-none transition-colors ${className}`}
      style={{
        backgroundColor: meta.bgColor,
        borderColor: meta.borderColor,
        color: meta.color,
      }}
      title={`Cryptographic Primitive: ${meta.name} (${meta.tag})`}
    >
      <span className="font-bold tracking-wider">{meta.tag}</span>
      {!showTagOnly && <span className="text-[12px] opacity-85">{meta.name}</span>}
    </span>
  );
};
