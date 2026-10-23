import React, { useState } from 'react';
import { CornerDownRight } from 'lucide-react';

export interface DisasmLine {
  address: string;
  bytes: string;
  mnemonic: string;
  op_str: string;
  is_influential?: boolean;
  is_jump?: boolean;
  jump_target?: string;
  matched_constant?: string;
  comment?: string;
}

interface DisassemblyViewerProps {
  instructions: DisasmLine[];
  className?: string;
  onLineClick?: (line: DisasmLine) => void;
}

// Highlight hex literals and constants in operand strings
function renderOperands(opStr: string) {
  if (!opStr) return null;
  // Match 0x[0-9a-fA-F]+ or numbers
  const parts = opStr.split(/(0x[0-9a-fA-F]+|#[0-9a-fA-F]+|\$[0-9a-fA-F]+|\b\d+\b)/g);
  return (
    <span>
      {parts.map((part, i) => {
        const isHexOrNum = /^(0x[0-9a-fA-F]+|#[0-9a-fA-F]+|\$[0-9a-fA-F]+|\b\d+\b)$/.test(part);
        if (isHexOrNum) {
          return (
            <span key={i} className="text-accent font-semibold">
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

export const DisassemblyViewer: React.FC<DisassemblyViewerProps> = ({
  instructions,
  className = '',
  onLineClick,
}) => {
  const [selectedAddr, setSelectedAddr] = useState<string | null>(null);

  const handleSelect = (line: DisasmLine) => {
    setSelectedAddr(line.address);
    if (onLineClick) onLineClick(line);
  };

  return (
    <div 
      className={`border border-border-default bg-bg-base rounded-[6px] overflow-hidden font-mono text-[12px] flex flex-col ${className}`}
    >
      {/* Header bar */}
      <div className="h-7 bg-bg-surface border-b border-border-default px-3 flex items-center justify-between text-[12px] font-mono uppercase tracking-[0.04em] text-text-secondary select-none">
        <div className="flex items-center gap-6">
          <span className="w-24">Address</span>
          <span className="w-24">Bytes</span>
          <span className="w-16">Mnem</span>
          <span>Operands</span>
        </div>
        <div className="flex items-center gap-3 text-text-disabled">
          <span className="tabular-nums">{instructions.length} insns</span>
          <span>•</span>
          <span>Disassembly View</span>
        </div>
      </div>

      {/* Disassembly rows */}
      <div className="overflow-y-auto max-h-[520px] select-text">
        {instructions.map((insn, idx) => {
          const isSelected = selectedAddr === insn.address;
          const isInfluential = insn.is_influential || ['xor', 'ror', 'rol', 'aes', 'sha'].some(k => insn.mnemonic.toLowerCase().includes(k));

          return (
            <div
              key={idx}
              onClick={() => handleSelect(insn)}
              className={`flex items-center px-3 py-1 cursor-pointer transition-colors relative border-b border-border-default/40 hover:bg-bg-raised/70 ${
                isSelected ? 'bg-bg-raised text-text-primary' : ''
              } ${isInfluential ? 'bg-accent/5' : ''}`}
            >
              {/* 3px left accent bar for influential instructions */}
              {isInfluential && (
                <div 
                  className="absolute left-0 top-0 bottom-0 w-[3px] bg-accent" 
                  title="Influential instruction (high SHAP attribution or crypto primitive token)"
                />
              )}

              {/* Gutter with Jump Arrow / Address */}
              <div className="w-24 flex items-center gap-1.5 text-text-secondary select-none shrink-0">
                {insn.is_jump ? (
                  <CornerDownRight className="w-3.5 h-3.5 text-status-warning shrink-0" strokeWidth={1.5} />
                ) : (
                  <span className="w-3.5" />
                )}
                <span className="tabular-nums text-text-secondary hover:text-text-primary">
                  {insn.address}
                </span>
              </div>

              {/* Dimmed Hex Bytes Column */}
              <div className="w-24 text-text-disabled shrink-0 tabular-nums truncate">
                {insn.bytes}
              </div>

              {/* Mnemonic (in text/primary) */}
              <div className={`w-16 font-semibold shrink-0 ${
                isInfluential ? 'text-accent' : 'text-text-primary'
              }`}>
                {insn.mnemonic}
              </div>

              {/* Operands (in text/secondary) & Matched Constants Chip */}
              <div className="flex-1 flex items-center justify-between gap-4 overflow-hidden">
                <span className="text-text-secondary truncate">
                  {renderOperands(insn.op_str)}
                </span>

                {insn.matched_constant && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded-[4px] bg-status-warning/15 border border-status-warning/40 text-status-warning text-[12px] font-mono shrink-0">
                    {insn.matched_constant}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
