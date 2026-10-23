import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  fetchFunctionDisasm, 
  fetchFunctionCfg, 
  fetchFunctionDfg, 
  fetchFunctionExplain 
} from '@/lib/api';
import { 
  ArrowLeft, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react';
import { DisassemblyViewer, DisasmLine } from '@/components/ui/DisassemblyViewer';
import { PrimitiveBadge } from '@/components/ui/PrimitiveBadge';
import { ConfidenceBar } from '@/components/ui/ConfidenceBar';
import { LowConfidenceWarning } from '@/components/ui/StateViews';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

export const FunctionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'prediction' | 'explanation' | 'cfg' | 'dfg' | 'signature_vs_ml' | 'raw_features'>('prediction');

  const { data: disasm } = useQuery({
    queryKey: ['disasm', id],
    queryFn: () => (id ? fetchFunctionDisasm(id) : null),
    enabled: !!id,
  });

  const { data: cfg } = useQuery({
    queryKey: ['cfg', id],
    queryFn: () => (id ? fetchFunctionCfg(id) : null),
    enabled: !!id,
  });

  const { data: dfg } = useQuery({
    queryKey: ['dfg', id],
    queryFn: () => (id ? fetchFunctionDfg(id) : null),
    enabled: !!id,
  });

  const { data: explain } = useQuery({
    queryKey: ['explain', id],
    queryFn: () => (id ? fetchFunctionExplain(id) : null),
    enabled: !!id,
  });

  // Mocked/realistic fallback disassembly if active target is loaded
  const sampleDisasm: DisasmLine[] = disasm?.instructions || [
    { address: '0x00401A20', bytes: '55', mnemonic: 'push', op_str: 'rbp' },
    { address: '0x00401A21', bytes: '48 89 e5', mnemonic: 'mov', op_str: 'rbp, rsp' },
    { address: '0x00401A24', bytes: '48 83 ec 40', mnemonic: 'sub', op_str: 'rsp, 0x40' },
    { address: '0x00401A28', bytes: '48 89 7d d8', mnemonic: 'mov', op_str: 'qword ptr [rbp - 0x28], rdi' },
    { address: '0x00401A2C', bytes: '48 8b 45 d8', mnemonic: 'mov', op_str: 'rax, qword ptr [rbp - 0x28]' },
    { address: '0x00401A30', bytes: '0f b6 00', mnemonic: 'movzx', op_str: 'eax, byte ptr [rax]', is_influential: true },
    { address: '0x00401A33', bytes: '89 45 fc', mnemonic: 'mov', op_str: 'dword ptr [rbp - 4], eax' },
    { address: '0x00401A36', bytes: '8b 45 fc', mnemonic: 'mov', op_str: 'eax, dword ptr [rbp - 4]' },
    { address: '0x00401A39', bytes: '48 8d 15 c0 a5', mnemonic: 'lea', op_str: 'rdx, [rip + 0xa5c0]', matched_constant: 'AES S-box byte 0x63' },
    { address: '0x00401A40', bytes: '0f b6 04 02', mnemonic: 'movzx', op_str: 'eax, byte ptr [rdx + rax]', is_influential: true },
    { address: '0x00401A44', bytes: '31 45 f0', mnemonic: 'xor', op_str: 'dword ptr [rbp - 0x10], eax', is_influential: true },
    { address: '0x00401A47', bytes: 'c1 c8 08', mnemonic: 'ror', op_str: 'eax, 0x8', is_influential: true },
    { address: '0x00401A4A', bytes: '83 7d f8 0a', mnemonic: 'cmp', op_str: 'dword ptr [rbp - 8], 0xa' },
    { address: '0x00401A4E', bytes: '7c d8', mnemonic: 'jl', op_str: '0x00401A28', is_jump: true, jump_target: '0x00401A28' },
    { address: '0x00401A50', bytes: 'c9', mnemonic: 'leave', op_str: '' },
    { address: '0x00401A51', bytes: 'c3', mnemonic: 'ret', op_str: '' },
  ];

  const prim = explain?.primitive || 'AES';
  const conf = explain?.confidence || 0.94;
  const isLowConfidence = conf < 0.65;

  // React Flow CFG setup with semantic variables
  const cfgNodes = (cfg?.blocks || [
    { id: '1', hex_start: '0x00401A20', instruction_count: 5, terminator_type: 'Conditional Jump' },
    { id: '2', hex_start: '0x00401A36', instruction_count: 8, terminator_type: 'Loop Back-edge' },
    { id: '3', hex_start: '0x00401A50', instruction_count: 2, terminator_type: 'Return' },
  ]).map((b: any, index: number) => ({
    id: b.id.toString(),
    position: { x: (index % 2) * 220 + 30, y: Math.floor(index / 2) * 160 + 30 },
    data: {
      label: (
        <div className="font-mono text-[12px] text-left p-1 text-text-primary">
          <div className="font-bold text-accent border-b border-border-default pb-0.5 mb-1">{b.hex_start}</div>
          <div className="text-text-secondary">{b.instruction_count} instructions</div>
          <div className="text-text-disabled text-[12px] mt-0.5">{b.terminator_type}</div>
        </div>
      ),
    },
    style: {
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-default)',
      borderRadius: '4px',
      width: 170,
    },
  }));

  const cfgEdges = [
    { id: 'e1-2', source: '1', target: '2', label: 'fallthrough', style: { stroke: 'var(--status-info)' } },
    { id: 'e2-1', source: '2', target: '1', label: 'back-edge (loop)', animated: true, style: { stroke: 'var(--accent)' } },
    { id: 'e2-3', source: '2', target: '3', label: 'exit', style: { stroke: 'var(--status-success)' } },
  ];

  return (
    <div className="space-y-4 max-w-7xl mx-auto font-mono">
      {/* Top Header */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-[4px] border border-border-default hover:bg-bg-raised text-text-secondary hover:text-text-primary transition min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
            title="Go back"
          >
            <ArrowLeft className="w-4 h-4" strokeWidth={1.5} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-[18px] text-text-primary">{id || 'sub_00401A20'}</span>
              <PrimitiveBadge primitive={prim} />
              {isLowConfidence && (
                <span className="px-2 py-0.5 rounded-[4px] bg-status-danger/20 text-status-danger text-[12px] font-bold">
                  LOW CONFIDENCE
                </span>
              )}
            </div>
            <div className="text-[12px] text-text-secondary mt-1">
              1,284 B • 321 instructions • Cyclomatic Complexity: 12
            </div>
          </div>
        </div>

        {/* Confidence metric indicator */}
        <div className="flex items-center gap-3 px-3 py-2 bg-bg-raised border border-border-default rounded-[4px] text-[12px]">
          <span className="text-text-secondary">Model Confidence:</span>
          <ConfidenceBar confidence={conf} threshold={0.65} />
        </div>
      </div>

      {isLowConfidence && (
        <LowConfidenceWarning
          confidence={conf}
          threshold={0.65}
          suggestedPrimitive={prim}
        />
      )}

      {/* Split Pane: Left 55% Disassembly vs Right 45% Analysis Tabs (Max 2 Containers) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 55% (7 Cols) Disassembly View */}
        <div className="lg:col-span-7 flex flex-col space-y-2">
          <DisassemblyViewer instructions={sampleDisasm} />
        </div>

        {/* Right 45% (5 Cols) Multi-Tab Analysis Container */}
        <div className="lg:col-span-5 border border-border-default bg-bg-surface rounded-[6px] flex flex-col overflow-hidden">
          {/* Tabs Navigation Header */}
          <div className="h-10 bg-bg-raised border-b border-border-default px-2 flex items-center gap-1 overflow-x-auto text-[12px]">
            {[
              { id: 'prediction', label: 'Prediction' },
              { id: 'explanation', label: 'SHAP / Attn' },
              { id: 'cfg', label: 'CFG' },
              { id: 'dfg', label: 'DFG' },
              { id: 'signature_vs_ml', label: 'ML vs Signature' },
              { id: 'raw_features', label: 'Raw Features' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-[4px] transition whitespace-nowrap cursor-pointer min-h-[36px] ${
                  activeTab === tab.id
                    ? 'bg-bg-surface text-accent font-bold border border-border-default'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Body */}
          <div className="p-5 flex-1 overflow-y-auto max-h-[520px] text-[12px]">
            {/* Tab 1: Hierarchical Prediction Path */}
            {activeTab === 'prediction' && (
              <div className="space-y-4">
                <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-secondary block border-b border-border-default pb-1">
                  Hierarchical Classification Route
                </span>

                <div className="space-y-3 font-mono">
                  {/* L1 */}
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Level 1 (Crypto vs Non-crypto):</span>
                      <span className="text-status-success font-bold">CRYPTO</span>
                    </div>
                    <div className="flex justify-between items-center text-[12px]">
                      <span className="text-text-disabled">Confidence (Threshold 0.50):</span>
                      <span className="tabular-nums font-semibold">0.99</span>
                    </div>
                  </div>

                  {/* L2 */}
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Level 2 (Family):</span>
                      <span className="text-text-primary font-bold">SYMMETRIC CIPHER</span>
                    </div>
                    <div className="flex justify-between items-center text-[12px]">
                      <span className="text-text-disabled">Confidence (Threshold 0.60):</span>
                      <span className="tabular-nums font-semibold">0.97</span>
                    </div>
                  </div>

                  {/* L3 */}
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">Level 3 (Primitive):</span>
                      <span className="text-accent font-bold">AES</span>
                    </div>
                    <div className="flex justify-between items-center text-[12px]">
                      <span className="text-text-disabled">Confidence (Threshold 0.65):</span>
                      <span className="text-accent font-bold tabular-nums">0.94</span>
                    </div>
                  </div>
                </div>

                <div className="p-3.5 bg-bg-raised border border-border-default rounded-[4px] space-y-1 text-text-secondary font-sans text-[12px] leading-relaxed">
                  <span className="font-semibold text-text-primary block font-mono">Classification Rationale</span>
                  Prediction routed via Level 1 binary detector, through Symmetric Family, terminating on AES with 0.94 confidence. Function displays 10 iterative unrolled rounds, S-box byte lookups, and cyclic rotate operations.
                </div>
              </div>
            )}

            {/* Tab 2: SHAP Feature Importance */}
            {activeTab === 'explanation' && (
              <div className="space-y-4">
                <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-secondary block border-b border-border-default pb-1">
                  Top SHAP Attributions (TreeExplainer)
                </span>

                <div className="space-y-2">
                  {[
                    { feat: 'insn_norm_AND_OR_XOR_ratio', val: 0.42, group: 'Instruction' },
                    { feat: 'dfg_xor_rotate_chains', val: 0.31, group: 'DFG' },
                    { feat: 'byte_ngram_entropy', val: 0.22, group: 'Byte' },
                    { feat: 'cfg_cyclomatic_complexity', val: 0.15, group: 'CFG' },
                    { feat: 'raw_branch_ratio', val: -0.08, group: 'Instruction' },
                  ].map((f, i) => (
                    <div key={i} className="p-2.5 bg-bg-raised border border-border-default rounded-[4px] font-mono text-[12px] space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-text-primary">{f.feat}</span>
                        <span className={`font-bold tabular-nums ${f.val > 0 ? 'text-status-success' : 'text-status-danger'}`}>
                          {f.val > 0 ? `+${f.val}` : f.val}
                        </span>
                      </div>
                      <div className="flex justify-between text-text-disabled text-[12px]">
                        <span>Group: {f.group}</span>
                        <span>{f.val > 0 ? 'Positive evidence' : 'Negative dampening'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 3: CFG */}
            {activeTab === 'cfg' && (
              <div className="h-80 w-full border border-border-default bg-bg-base rounded-[4px] overflow-hidden">
                <ReactFlow nodes={cfgNodes} edges={cfgEdges} fitView>
                  <Background color="var(--border-default)" gap={16} />
                  <Controls className="bg-bg-surface border-border-default text-text-primary" />
                </ReactFlow>
              </div>
            )}

            {/* Tab 4: DFG */}
            {activeTab === 'dfg' && (
              <div className="space-y-3 font-mono">
                <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-secondary block border-b border-border-default pb-1">
                  Data Flow Graph Def-Use Metrics
                </span>
                <div className="grid grid-cols-2 gap-3 text-[12px]">
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                    <span className="text-[12px] text-text-disabled uppercase block">Def-Use Chains</span>
                    <span className="text-accent font-bold text-[16px] tabular-nums">14</span>
                  </div>
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                    <span className="text-[12px] text-text-disabled uppercase block">Table Lookups</span>
                    <span className="text-status-info font-bold text-[16px] tabular-nums">4</span>
                  </div>
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                    <span className="text-[12px] text-text-disabled uppercase block">XOR-Rotate Sequences</span>
                    <span className="text-status-success font-bold text-[16px] tabular-nums">8</span>
                  </div>
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px]">
                    <span className="text-[12px] text-text-disabled uppercase block">Max Dependency Depth</span>
                    <span className="text-status-warning font-bold text-[16px] tabular-nums">6</span>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 5: Signature vs ML Comparison */}
            {activeTab === 'signature_vs_ml' && (
              <div className="space-y-3 font-mono">
                <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-secondary block border-b border-border-default pb-1">
                  Signature Scanner vs ML Model Comparison
                </span>

                <div className="grid grid-cols-2 gap-3 text-[12px]">
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <span className="text-[12px] text-text-disabled uppercase block">Static Constant Match</span>
                    <span className="font-bold text-status-warning">AES S-box (0x63)</span>
                    <p className="text-[12px] text-text-secondary mt-1">Found in .rodata constant pool</p>
                  </div>
                  <div className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1">
                    <span className="text-[12px] text-text-disabled uppercase block">Machine Learning (RF/TF)</span>
                    <span className="font-bold text-accent">AES (0.94 Conf)</span>
                    <p className="text-[12px] text-text-secondary mt-1">Based on instruction sequence & CFG</p>
                  </div>
                </div>

                <div className="p-3 bg-status-success/10 border border-status-success/30 rounded-[4px] text-status-success text-[12px] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" strokeWidth={1.5} />
                  <span>Concordance: Both signature scanner and ML classifier agree on AES primitive.</span>
                </div>
              </div>
            )}

            {/* Tab 6: Raw Features Table */}
            {activeTab === 'raw_features' && (
              <div className="space-y-2 font-mono">
                <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-secondary block border-b border-border-default pb-1">
                  Extracted Feature Vector Values
                </span>
                <table className="w-full text-left text-[12px] table-dense">
                  <thead>
                    <tr className="border-b border-border-default text-text-disabled text-[12px]">
                      <th className="py-1">Feature Name</th>
                      <th className="py-1 text-right">Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-default text-[12px]">
                    <tr><td>byte_entropy_shannon</td><td className="text-right text-accent tabular-nums">7.142</td></tr>
                    <tr><td>insn_xor_ratio</td><td className="text-right text-text-primary tabular-nums">0.184</td></tr>
                    <tr><td>insn_rotate_ratio</td><td className="text-right text-text-primary tabular-nums">0.092</td></tr>
                    <tr><td>cfg_cyclomatic_complexity</td><td className="text-right text-text-primary tabular-nums">12</td></tr>
                    <tr><td>dfg_def_use_depth</td><td className="text-right text-text-primary tabular-nums">6</td></tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
