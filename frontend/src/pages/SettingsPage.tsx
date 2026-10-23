import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { 
  Sun, 
  Moon, 
  Cpu, 
  HardDrive, 
  Sliders, 
  ShieldCheck, 
  BookOpen 
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useAppStore();
  const [rowDensity, setRowDensity] = useState<'dense' | 'comfortable'>('dense');

  return (
    <div className="space-y-6 max-w-5xl mx-auto font-mono">
      {/* Title */}
      <div className="border-b border-border-default pb-3">
        <h1 className="text-[18px] font-bold uppercase tracking-tight text-text-primary">
          System & Reverse Engineering Environment Settings
        </h1>
        <span className="text-[12px] text-text-secondary">
          Configure display density, cross-compiler paths, model storage directories, and defensive ethics parameters
        </span>
      </div>

      {/* 1. Appearance & Table Density */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
        <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
          1. Appearance & Interface Density
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 bg-bg-raised border border-border-default rounded-[4px]">
            <div>
              <span className="font-semibold text-text-primary block">Color Theme</span>
              <span className="text-[12px] text-text-secondary">WCAG AA high contrast</span>
            </div>
            <button
              onClick={toggleTheme}
              className="flex items-center gap-1.5 px-3 py-2 bg-bg-surface border border-border-default rounded-[4px] text-[12px] hover:border-accent text-text-primary min-h-[44px] cursor-pointer"
            >
              {theme === 'dark' ? <Moon className="w-4 h-4" strokeWidth={1.5} /> : <Sun className="w-4 h-4 text-status-warning" strokeWidth={1.5} />}
              <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
            </button>
          </div>

          <div className="flex items-center justify-between p-3 bg-bg-raised border border-border-default rounded-[4px]">
            <div>
              <span className="font-semibold text-text-primary block">Table Row Density</span>
              <span className="text-[12px] text-text-secondary">28px dense vs 40px comfortable</span>
            </div>
            <div className="flex rounded-[4px] border border-border-default bg-bg-surface p-1 text-[12px]">
              <button
                onClick={() => setRowDensity('dense')}
                className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${rowDensity === 'dense' ? 'bg-accent text-accent-on font-bold' : 'text-text-secondary'}`}
              >
                28px
              </button>
              <button
                onClick={() => setRowDensity('comfortable')}
                className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${rowDensity === 'comfortable' ? 'bg-accent text-accent-on font-bold' : 'text-text-secondary'}`}
              >
                40px
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Paths (Toolchains & Model Storage) */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
        <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
          2. Storage & Toolchain Executable Paths
        </span>

        <div className="space-y-2 text-[12px]">
          <div className="flex justify-between items-center p-2.5 bg-bg-raised border border-border-default rounded-[4px]">
            <span className="text-text-secondary">SQLite Database File:</span>
            <span className="text-text-primary font-bold">./cryptoscope.db</span>
          </div>
          <div className="flex justify-between items-center p-2.5 bg-bg-raised border border-border-default rounded-[4px]">
            <span className="text-text-secondary">AArch64 Cross Compiler:</span>
            <span className="text-status-success font-bold">/usr/bin/aarch64-linux-gnu-gcc</span>
          </div>
          <div className="flex justify-between items-center p-2.5 bg-bg-raised border border-border-default rounded-[4px]">
            <span className="text-text-secondary">Model Checkpoint Directory:</span>
            <span className="text-text-primary font-bold">./backend/app/models/saved</span>
          </div>
          <div className="flex justify-between items-center p-2.5 bg-bg-raised border border-border-default rounded-[4px]">
            <span className="text-text-secondary">Dataset Manifests Directory:</span>
            <span className="text-text-primary font-bold">./datasets/manifests</span>
          </div>
        </div>
      </div>

      {/* 3. Performance & Concurrency */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4 text-[12px]">
        <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
          3. Performance & Concurrency Allocation
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[12px]">
          <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
            <span className="text-text-secondary block">Disassembly Workers:</span>
            <span className="font-bold text-accent text-[14px]">8 Threads (Parallel)</span>
          </div>
          <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
            <span className="text-text-secondary block">PyTorch Execution Device:</span>
            <span className="font-bold text-status-success text-[14px]">CPU / AVX2 Accelerated</span>
          </div>
        </div>
      </div>

      {/* 4. About & Defensive Scope Statement */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-3 text-[12px]">
        <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-disabled block border-b border-border-default pb-1">
          4. About, Paper Citation & Defensive Use Notice
        </span>

        <p className="text-[12px] text-text-secondary leading-relaxed font-sans">
          <strong>CryptoScope v1.0.0</strong> implements the research publication:
          <br />
          <em>"AI/ML-Based Identification of Cryptographic Primitives and Protocols in Multi-Architecture Firmware"</em>.
        </p>

        <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] text-[12px] text-text-secondary font-mono leading-relaxed">
          <span className="text-text-primary font-bold block mb-1">Ethical Scope & Security Boundaries:</span>
          This software is engineered exclusively as an offline, non-destructive, defensive inspection tool. It classifies algorithms and reconstructs protocol patterns for SBOM auditing and vulnerability assessment. It contains zero exploit generation, binary patching, or execution tampering capabilities.
        </div>
      </div>
    </div>
  );
};
