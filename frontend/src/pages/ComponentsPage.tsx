import React, { useState } from 'react';
import { 
  Code2, 
  Layers, 
  Terminal, 
  Database, 
  CheckCircle2, 
  AlertTriangle, 
  Play, 
  Filter, 
  RefreshCw 
} from 'lucide-react';
import { StatStrip } from '@/components/ui/StatStrip';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';
import { DisassemblyViewer, DisasmLine } from '@/components/ui/DisassemblyViewer';
import { PrimitiveBadge } from '@/components/ui/PrimitiveBadge';
import { ConfidenceBar } from '@/components/ui/ConfidenceBar';
import { 
  FlatSkeleton, 
  EmptyState, 
  ErrorState, 
  FilteredZeroState, 
  FailedJobState, 
  MissingToolchainState, 
  LowConfidenceWarning, 
  OfflineBackendState, 
  UnsupportedIsaWarning, 
  ScientificCaveatBanner 
} from '@/components/ui/StateViews';

interface DemoRow {
  id: string;
  address: string;
  name: string;
  primitive: string;
  confidence: number;
  instructions: number;
  cyclomatic: number;
}

const DEMO_TABLE_DATA: DemoRow[] = [
  { id: '1', address: '0x00041200', name: 'aes_encrypt_block', primitive: 'AES', confidence: 0.96, instructions: 184, cyclomatic: 8 },
  { id: '2', address: '0x000418A0', name: 'sha256_transform', primitive: 'SHA-256', confidence: 0.98, instructions: 312, cyclomatic: 4 },
  { id: '3', address: '0x00042450', name: 'chacha20_core', primitive: 'ChaCha20', confidence: 0.94, instructions: 128, cyclomatic: 2 },
  { id: '4', address: '0x00043180', name: 'mod_exp_montgomery', primitive: 'RSA', confidence: 0.91, instructions: 512, cyclomatic: 14 },
  { id: '5', address: '0x00043E00', name: 'poly1305_block', primitive: 'HMAC', confidence: 0.88, instructions: 96, cyclomatic: 3 },
  { id: '6', address: '0x00044500', name: 'curve25519_scalarmult', primitive: 'ECC', confidence: 0.95, instructions: 640, cyclomatic: 18 },
  { id: '7', address: '0x00045200', name: 'json_parse_token', primitive: 'Non-Crypto', confidence: 0.99, instructions: 220, cyclomatic: 12 },
];

const DEMO_DISASM: DisasmLine[] = [
  { address: '0x00041200', bytes: '55', mnemonic: 'push', op_str: 'rbp' },
  { address: '0x00041201', bytes: '48 89 e5', mnemonic: 'mov', op_str: 'rbp, rsp' },
  { address: '0x00041204', bytes: '48 81 ec 80 00 00 00', mnemonic: 'sub', op_str: 'rsp, 0x80' },
  { address: '0x0004120b', bytes: '48 89 7d f8', mnemonic: 'mov', op_str: 'QWORD PTR [rbp-0x8], rdi' },
  { address: '0x0004120f', bytes: '66 0f 38 dc 07', mnemonic: 'aesenc', op_str: 'xmm0, XMMWORD PTR [rdi]', is_influential: true, matched_constant: 'AES S-box: 0x63' },
  { address: '0x00041214', bytes: '66 0f 38 dc 47 10', mnemonic: 'aesenc', op_str: 'xmm0, XMMWORD PTR [rdi+0x10]', is_influential: true },
  { address: '0x0004121a', bytes: '66 0f 38 df 47 20', mnemonic: 'aesenclast', op_str: 'xmm0, XMMWORD PTR [rdi+0x20]', is_influential: true },
  { address: '0x00041220', bytes: '31 c0', mnemonic: 'xor', op_str: 'eax, eax', is_influential: true },
  { address: '0x00041222', bytes: 'eb 0a', mnemonic: 'jmp', op_str: '0x0004122e', is_jump: true, jump_target: '0x0004122e' },
  { address: '0x0004122e', bytes: 'c9', mnemonic: 'leave', op_str: '' },
  { address: '0x0004122f', bytes: 'c3', mnemonic: 'ret', op_str: '' },
];

export const ComponentsPage: React.FC = () => {
  const [devMode, setDevMode] = useState(true);
  const [selectedRowId, setSelectedRowId] = useState<string>('1');
  const [activeTab, setActiveTab] = useState<'tables' | 'disasm' | 'controls' | 'states'>('tables');

  const tableColumns: ColumnDef<DemoRow>[] = [
    { key: 'address', label: 'Address', width: 130, isSticky: true, isMono: true },
    { key: 'name', label: 'Function Symbol', width: 220, isMono: true },
    {
      key: 'primitive',
      label: 'Primitive',
      width: 130,
      render: (val: string) => <PrimitiveBadge primitive={val} />,
    },
    {
      key: 'confidence',
      label: 'Confidence',
      width: 170,
      render: (val: number) => <ConfidenceBar confidence={val} threshold={0.5} />,
    },
    {
      key: 'instructions',
      label: 'Instructions',
      width: 120,
      align: 'right',
      render: (val: number) => val.toLocaleString(),
    },
    {
      key: 'cyclomatic',
      label: 'Cyclomatic',
      width: 100,
      align: 'right',
      render: (val: number) => val,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border-default">
        <div>
          <h1 className="text-[18px] font-mono font-bold tracking-tight text-text-primary">
            Component Library & Dev Annotations
          </h1>
          <p className="text-[12px] text-text-secondary mt-1">
            Production reverse-engineering tooling components with interactive states and specs.
          </p>
        </div>

        {/* Dev Mode Switch */}
        <button
          onClick={() => setDevMode(!devMode)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] border font-mono text-[12px] transition cursor-pointer min-h-[44px] ${
            devMode
              ? 'bg-accent/15 border-accent text-accent font-semibold'
              : 'bg-bg-raised border-border-default text-text-secondary hover:text-text-primary'
          }`}
        >
          <Code2 className="w-4 h-4" strokeWidth={1.5} />
          <span>Dev-Mode Annotations: {devMode ? 'ACTIVE' : 'OFF'}</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-default gap-1 font-mono text-[12px]">
        {[
          { key: 'tables', label: '28px Dense Tables & Strips' },
          { key: 'disasm', label: 'Disassembly Viewer' },
          { key: 'controls', label: 'Buttons & Controls' },
          { key: 'states', label: 'All 9 System States' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 border-b-2 font-medium transition cursor-pointer min-h-[44px] ${
              activeTab === tab.key
                ? 'border-accent text-accent bg-bg-raised/40 font-semibold'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Dense Data Table & Stat Strip */}
      {activeTab === 'tables' && (
        <div className="space-y-6">
          {/* Stat Strip */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[12px] uppercase font-bold text-text-secondary tracking-wider">
                Bordered Stat Strip (Replaces Generic Cards)
              </span>
              {devMode && (
                <span className="font-mono text-[12px] text-accent">
                  Component: &lt;StatStrip items=[...] /&gt; • 1px border • single container
                </span>
              )}
            </div>
            <StatStrip
              items={[
                { label: 'Firmware Analyzed', value: '214 targets', subtext: '+12 this week' },
                { label: 'Functions Recovered', value: '48,912', subtext: 'Across 5 ISAs' },
                { label: 'Verified Datasets', value: '3 suites', subtext: '50 binaries' },
                { label: 'Active Classifier', value: 'Hierarchical L1-L3', subtext: 'F1: 0.955', highlight: true },
              ]}
            />
          </div>

          {/* 28px Dense Data Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[12px] uppercase font-bold text-text-secondary tracking-wider">
                Professional Data Table (28px Dense Rows, Sticky Header & First Col, Drag Resize)
              </span>
              {devMode && (
                <span className="font-mono text-[12px] text-accent">
                  Row Height: 28px • Column Resizing • Tabular Numerals • Sticky First Col
                </span>
              )}
            </div>

            <DataTable
              columns={tableColumns}
              data={DEMO_TABLE_DATA}
              selectedId={selectedRowId}
              onRowClick={(row) => setSelectedRowId(row.id)}
              idKey="id"
            />
            <div className="text-[12px] font-mono text-text-disabled flex items-center justify-between px-1">
              <span>Click any row to select • Drag vertical handles on table headers to resize columns</span>
              <span>Showing 7 of 7 demo functions</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Disassembly Viewer */}
      {activeTab === 'disasm' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[12px] uppercase font-bold text-text-secondary tracking-wider">
              Tooling Disassembly Viewer (CapStone Multi-ISA)
            </span>
            {devMode && (
              <span className="font-mono text-[12px] text-accent">
                3px Accent Bar • Dimmed Hex Bytes • Immediate Highlight • Matched Constant Chips
              </span>
            )}
          </div>

          <DisassemblyViewer instructions={DEMO_DISASM} />
        </div>
      )}

      {/* Tab 3: Buttons & Controls across all 5 states */}
      {activeTab === 'controls' && (
        <div className="space-y-6">
          <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="font-mono text-[12px] uppercase font-bold text-text-primary tracking-wider">
                Control States Matrix (4px Radius, 2px Accent Focus Rings, ≥44px Mobile Targets)
              </span>
              <span className="font-mono text-[12px] text-text-disabled">0 Gradients • 0 Pill Buttons</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-5 gap-4 font-mono text-[12px]">
              {/* Default */}
              <div className="space-y-3">
                <span className="text-text-disabled block uppercase font-bold">1. Default</span>
                <button className="w-full py-2 px-3 rounded-[4px] bg-accent text-accent-on font-semibold hover:bg-accent-hover transition cursor-pointer min-h-[44px]">
                  Primary Action
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] bg-bg-raised border border-border-default text-text-primary hover:bg-bg-surface transition cursor-pointer min-h-[44px]">
                  Secondary
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] border border-status-danger/60 text-status-danger hover:bg-status-danger/10 transition cursor-pointer min-h-[44px]">
                  Danger
                </button>
              </div>

              {/* Hover */}
              <div className="space-y-3">
                <span className="text-text-disabled block uppercase font-bold">2. Hover State</span>
                <button className="w-full py-2 px-3 rounded-[4px] bg-accent-hover text-accent-on font-semibold min-h-[44px]">
                  Primary Action
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] bg-bg-surface border border-border-strong text-text-primary min-h-[44px]">
                  Secondary
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] border border-status-danger bg-status-danger/15 text-status-danger min-h-[44px]">
                  Danger
                </button>
              </div>

              {/* Active */}
              <div className="space-y-3">
                <span className="text-text-disabled block uppercase font-bold">3. Active / Pressed</span>
                <button className="w-full py-2 px-3 rounded-[4px] bg-accent text-accent-on opacity-90 scale-[0.98] font-semibold min-h-[44px]">
                  Primary Action
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] bg-bg-base border border-accent text-accent scale-[0.98] min-h-[44px]">
                  Secondary
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] bg-status-danger text-white scale-[0.98] min-h-[44px]">
                  Danger
                </button>
              </div>

              {/* Focus Ring */}
              <div className="space-y-3">
                <span className="text-text-disabled block uppercase font-bold">4. Focus Ring (2px)</span>
                <button className="w-full py-2 px-3 rounded-[4px] bg-accent text-accent-on font-semibold ring-2 ring-accent ring-offset-2 ring-offset-bg-base min-h-[44px]">
                  Primary Action
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] bg-bg-raised border border-border-default text-text-primary ring-2 ring-accent ring-offset-2 ring-offset-bg-base min-h-[44px]">
                  Secondary
                </button>
                <button className="w-full py-2 px-3 rounded-[4px] border border-status-danger text-status-danger ring-2 ring-status-danger ring-offset-2 ring-offset-bg-base min-h-[44px]">
                  Danger
                </button>
              </div>

              {/* Disabled */}
              <div className="space-y-3">
                <span className="text-text-disabled block uppercase font-bold">5. Disabled</span>
                <button disabled className="w-full py-2 px-3 rounded-[4px] bg-bg-raised border border-border-default text-text-disabled cursor-not-allowed min-h-[44px]">
                  Primary Action
                </button>
                <button disabled className="w-full py-2 px-3 rounded-[4px] bg-bg-raised border border-border-default text-text-disabled cursor-not-allowed min-h-[44px]">
                  Secondary
                </button>
                <button disabled className="w-full py-2 px-3 rounded-[4px] bg-bg-raised border border-border-default text-text-disabled cursor-not-allowed min-h-[44px]">
                  Danger
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: All 9 System States */}
      {activeTab === 'states' && (
        <div className="space-y-6">
          <div className="space-y-1">
            <h2 className="text-[14px] font-mono font-bold uppercase tracking-wider text-text-primary">
              System States & Warnings Catalog
            </h2>
            <p className="text-[12px] text-text-secondary">
              Every edge condition, network partition, compile failure, and analysis warning has a deterministic component.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Flat Skeleton */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">1. Loading State (Flat Skeleton)</span>
              <FlatSkeleton rows={3} />
            </div>

            {/* 2. Empty State */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">2. Empty State with Action</span>
              <EmptyState
                title="No Compiled Firmware Binaries"
                description="The dataset directory does not contain any compiled ELF binaries. Run the automated synthesis pipeline."
                actionText="Generate Synthetic Matrix"
                onAction={() => {}}
              />
            </div>

            {/* 3. Error with Retry */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">3. Error State with Detail & Retry</span>
              <ErrorState
                title="Capstone Disassembly Engine Exception"
                errorDetail="CS_ERR_ARCH: Architecture mismatch for offset 0x00041200 (Expected MIPS32-BE, found ARM64 EL0)"
                onRetry={() => {}}
              />
            </div>

            {/* 4. Filtered Zero */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">4. Filtered-to-Zero Results</span>
              <FilteredZeroState activeFiltersCount={2} onResetFilters={() => {}} />
            </div>

            {/* 5. Failed Job */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">5. Background Job Failure</span>
              <FailedJobState
                jobId="job-train-transformer-8f12a"
                stepName="Deep Transformer Epoch 4"
                errorMessage="CUDA out of memory while allocating tensor shape [64, 512, 128]"
                onRestart={() => {}}
              />
            </div>

            {/* 6. Missing Toolchain */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">6. Missing Toolchain Detection</span>
              <MissingToolchainState
                missingIsa="MIPS32 (Big-Endian)"
                installCommand="apt install -y gcc-mips-linux-gnu g++-mips-linux-gnu"
              />
            </div>

            {/* 7. Low Confidence Prediction */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">7. Low-Confidence Warning</span>
              <LowConfidenceWarning
                confidence={0.34}
                threshold={0.5}
                suggestedPrimitive="ChaCha20"
                onManualOverride={() => {}}
              />
            </div>

            {/* 8. Offline Backend */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">8. Offline Backend Notice</span>
              <OfflineBackendState onRetryConnection={() => {}} />
            </div>

            {/* 9. Unsupported ISA Warning */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2 lg:col-span-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">9. Unsupported Architecture Warning</span>
              <UnsupportedIsaWarning
                isa="Xtensa LX6 (ESP32)"
                targetFile="esp32_smartplug_fw.bin"
                onGhidraFallback={() => {}}
              />
            </div>

            {/* 10. Mandatory Scientific Caveat */}
            <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 space-y-2 lg:col-span-2">
              <span className="font-mono text-[12px] font-bold text-text-secondary block">10. Mandatory Scientific Static Analysis Caveat</span>
              <ScientificCaveatBanner />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
