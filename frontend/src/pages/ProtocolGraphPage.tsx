import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Network, 
  ChevronDown, 
  ChevronUp,
  ArrowRight,
  List,
  Maximize2
} from 'lucide-react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { fetchAnalyses, fetchAnalysisDetail } from '@/lib/api';
import { getPrimitiveMeta } from '@/lib/utils';
import { ScientificCaveatBanner } from '@/components/ui/StateViews';
import { PrimitiveBadge } from '@/components/ui/PrimitiveBadge';

export const ProtocolGraphPage: React.FC = () => {
  const { data: analyses } = useQuery({
    queryKey: ['analyses'],
    queryFn: fetchAnalyses,
  });

  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string>('');
  const [layoutMode, setLayoutMode] = useState<'hierarchical' | 'force'>('hierarchical');
  const [expandedPatternId, setExpandedPatternId] = useState<string | null>('PAT-001');
  const [mobileView, setMobileView] = useState<'list' | 'graph'>('list');

  const activeId = selectedAnalysisId || analyses?.[0]?.id;

  const { data: analysis } = useQuery({
    queryKey: ['analysis', activeId],
    queryFn: () => (activeId ? fetchAnalysisDetail(activeId) : null),
    enabled: !!activeId,
  });

  const rawNodes = analysis?.protocol_graph?.nodes || [];
  const rawEdges = analysis?.protocol_graph?.edges || [];

  const flowNodes = rawNodes.map((n, i) => {
    const meta = getPrimitiveMeta(n.data.primitive);
    const x = layoutMode === 'hierarchical' ? (i % 3) * 230 + 40 : (i % 4) * 200 + 40;
    const y = layoutMode === 'hierarchical' ? Math.floor(i / 3) * 140 + 40 : Math.floor(i / 4) * 160 + 40;

    return {
      id: n.id,
      position: { x, y },
      data: {
        label: (
          <div className="p-1 font-mono text-left select-none">
            <div className="flex items-center justify-between border-b border-border-default pb-1 mb-1">
              <span className="font-bold text-[12px]" style={{ color: meta.color }}>
                [{meta.tag}] {meta.name}
              </span>
              <span className="text-[12px] text-text-disabled">{n.data.hex_address}</span>
            </div>
            <div className="text-[12px] text-text-secondary truncate">{n.data.family}</div>
            <div className="text-[12px] text-accent font-semibold mt-0.5 tabular-nums">
              Confidence: {Math.round((n.data.confidence || 0.9) * 100)}%
            </div>
          </div>
        ),
      },
      style: {
        background: 'var(--bg-surface)',
        border: `1px solid ${meta.borderColor}`,
        borderRadius: '4px',
        color: 'var(--text-primary)',
        width: 190,
      },
    };
  });

  const flowEdges = rawEdges.map((e, idx) => ({
    id: `e-${idx}`,
    source: e.source,
    target: e.target,
    label: e.label || 'calls',
    animated: true,
    style: { stroke: 'var(--accent)', strokeWidth: 1.5 },
    labelStyle: { fill: 'var(--text-secondary)', fontSize: '12px', fontFamily: 'monospace' },
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Persistent Static Analysis Limitation Banner */}
      <ScientificCaveatBanner />

      {/* Top Header Bar & Layout Switcher */}
      <div className="border border-border-default bg-bg-surface rounded-[6px] p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Network className="w-5 h-5 text-accent" strokeWidth={1.5} />
          <div>
            <h1 className="text-[18px] font-bold text-text-primary tracking-tight uppercase">
              Protocol Graph Reconstruction
            </h1>
            <span className="text-[12px] text-text-secondary">
              Inter-procedural call topology and cryptographic primitive interaction graph
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Target binary selector */}
          <select
            value={activeId}
            onChange={(e) => setSelectedAnalysisId(e.target.value)}
            className="bg-bg-raised border border-border-default text-text-primary rounded-[4px] px-3 py-2 text-[12px] font-mono outline-none focus:border-accent min-h-[44px]"
          >
            {(analyses || []).map(a => (
              <option key={a.id} value={a.id}>
                {a.filename} ({a.isa})
              </option>
            ))}
          </select>

          {/* Layout switcher */}
          <div className="flex rounded-[4px] border border-border-default bg-bg-raised p-1 text-[12px]">
            <button
              onClick={() => setLayoutMode('hierarchical')}
              className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${layoutMode === 'hierarchical' ? 'bg-bg-surface text-accent font-bold border border-border-default' : 'text-text-secondary'}`}
            >
              Hierarchical
            </button>
            <button
              onClick={() => setLayoutMode('force')}
              className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${layoutMode === 'force' ? 'bg-bg-surface text-accent font-bold border border-border-default' : 'text-text-secondary'}`}
            >
              Force Directed
            </button>
          </div>

          {/* Mobile View Toggle */}
          <div className="md:hidden flex rounded-[4px] border border-border-default bg-bg-raised p-1 text-[12px]">
            <button
              onClick={() => setMobileView('list')}
              className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${mobileView === 'list' ? 'bg-bg-surface text-accent font-bold' : 'text-text-secondary'}`}
            >
              List Fallback
            </button>
            <button
              onClick={() => setMobileView('graph')}
              className={`px-3 py-1.5 rounded-[2px] transition cursor-pointer min-h-[36px] ${mobileView === 'graph' ? 'bg-bg-surface text-accent font-bold' : 'text-text-secondary'}`}
            >
              Canvas
            </button>
          </div>
        </div>
      </div>

      {/* Full-width Graph Canvas + Right 360px Sidebar (Max 2 Containers) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Full-width Canvas container */}
        <div className="lg:col-span-8 border border-border-default bg-bg-base rounded-[6px] h-[580px] overflow-hidden relative">
          {/* Mobile List Fallback view */}
          <div className={`md:hidden h-full overflow-y-auto p-4 space-y-3 bg-bg-surface ${mobileView === 'graph' ? 'hidden' : 'block'}`}>
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="font-bold uppercase tracking-wider text-[12px] text-text-primary">
                Call Graph Interactions (Mobile List View)
              </span>
              <span className="text-[12px] text-text-secondary">{rawEdges.length} edges</span>
            </div>

            <div className="space-y-2">
              {rawEdges.length === 0 ? (
                <div className="p-4 text-center text-text-disabled text-[12px]">No call graph edges detected.</div>
              ) : (
                rawEdges.map((edge, i) => (
                  <div key={i} className="p-3 bg-bg-raised border border-border-default rounded-[4px] flex items-center justify-between text-[12px]">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-accent">{edge.source}</span>
                      <ArrowRight className="w-4 h-4 text-text-disabled" strokeWidth={1.5} />
                      <span className="font-bold text-text-primary">{edge.target}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded-[4px] bg-bg-surface border border-border-default text-text-secondary font-mono text-[12px]">
                      {edge.label || 'calls'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Desktop Canvas (or mobile when graph is toggled) */}
          <div className={`h-full w-full ${mobileView === 'list' ? 'hidden md:block' : 'block'}`}>
            <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
              <Background color="var(--border-default)" gap={16} />
              <Controls className="bg-bg-surface border-border-default text-text-primary rounded-[4px]" />
              <MiniMap 
                nodeColor="var(--accent)" 
                maskColor="var(--bg-base)" 
                className="bg-bg-surface border border-border-default rounded-[4px]" 
              />
            </ReactFlow>
          </div>
        </div>

        {/* Right 360px Panel: Ranked Protocol Patterns & Security Observations Container */}
        <div className="lg:col-span-4 border border-border-default bg-bg-surface rounded-[6px] p-5 space-y-5 font-mono text-[12px]">
          {/* Ranked Protocol Patterns Panel */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Ranked Protocol Patterns
              </span>
              <span className="text-accent font-bold tabular-nums">
                {analysis?.patterns?.length || 0} Matches
              </span>
            </div>

            <div className="space-y-2.5 max-h-[260px] overflow-y-auto">
              {(!analysis?.patterns || analysis.patterns.length === 0) ? (
                <div className="p-3 bg-bg-raised text-text-disabled text-center text-[12px]">
                  No multi-primitive protocol pattern recognized in call chains.
                </div>
              ) : (
                analysis.patterns.map((pat) => {
                  const isExpanded = expandedPatternId === pat.id;
                  return (
                    <div key={pat.id} className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-2">
                      <div 
                        onClick={() => setExpandedPatternId(isExpanded ? null : pat.id)}
                        className="flex items-center justify-between cursor-pointer"
                      >
                        <span className="font-bold text-text-primary text-[12px]">{pat.pattern_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-[4px] bg-accent/15 border border-accent/40 text-accent font-bold text-[12px] tabular-nums">
                            {Math.round(pat.confidence * 100)}%
                          </span>
                          {isExpanded ? <ChevronUp className="w-4 h-4 text-text-secondary" strokeWidth={1.5} /> : <ChevronDown className="w-4 h-4 text-text-secondary" strokeWidth={1.5} />}
                        </div>
                      </div>

                      <p className="text-[12px] text-text-secondary font-sans leading-relaxed">
                        {pat.description}
                      </p>

                      {isExpanded && (
                        <div className="pt-2 border-t border-border-default space-y-1 text-[12px]">
                          <span className="text-text-disabled uppercase tracking-wider block">Evidence Chain:</span>
                          {pat.evidence.map((ev, i) => (
                            <div key={i} className="text-text-primary flex items-start gap-1">
                              <span className="text-accent">•</span>
                              <span>{ev}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Security Advisories List */}
          <div className="space-y-3 pt-3 border-t border-border-default">
            <div className="flex items-center justify-between border-b border-border-default pb-1.5">
              <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-text-primary">
                Defensive Advisories
              </span>
              <span className="text-status-warning font-bold text-[12px]">
                {analysis?.advisories?.length || 0} Findings
              </span>
            </div>

            <div className="space-y-2 max-h-[220px] overflow-y-auto">
              {(!analysis?.advisories || analysis.advisories.length === 0) ? (
                <div className="p-3 bg-bg-raised text-text-disabled text-center text-[12px]">
                  No weak or legacy algorithms identified.
                </div>
              ) : (
                analysis.advisories.map((adv) => (
                  <div key={adv.id} className="p-3 bg-bg-raised border border-border-default rounded-[4px] space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-text-primary text-[12px] truncate max-w-[200px]">{adv.title}</span>
                      <span className={`text-[12px] font-bold px-2 py-0.5 rounded-[4px] ${adv.severity === 'CRITICAL' ? 'bg-status-danger/20 text-status-danger' : 'bg-status-warning/20 text-status-warning'}`}>
                        {adv.severity}
                      </span>
                    </div>
                    <p className="text-[12px] text-text-secondary font-sans leading-snug">{adv.risk_summary}</p>
                    <div className="text-[12px] text-accent pt-0.5">
                      Remediation: {adv.remediation_guidance}
                    </div>
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
