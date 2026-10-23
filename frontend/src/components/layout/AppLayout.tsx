import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  Cpu, 
  Terminal, 
  Database, 
  Sliders, 
  BarChart2, 
  Layers, 
  History, 
  FileText, 
  Settings as SettingsIcon, 
  Sun, 
  Moon, 
  ChevronLeft, 
  ChevronRight,
  Activity,
  Network,
  Search,
  BookOpen,
  Code2
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth, fetchToolchainStatus, fetchJobStatus } from '@/lib/api';
import { CommandPalette } from '@/components/ui/CommandPalette';

interface NavGroup {
  caption: string;
  items: Array<{
    path: string;
    label: string;
    icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  }>;
}

const NAV_GROUPS: NavGroup[] = [
  {
    caption: 'ANALYSIS',
    items: [
      { path: '/', label: 'Dashboard', icon: Activity },
      { path: '/analyze', label: 'Analyze Firmware', icon: Terminal },
      { path: '/analyses', label: 'Results', icon: Layers },
      { path: '/protocol', label: 'Protocol Graph', icon: Network },
    ]
  },
  {
    caption: 'RESEARCH',
    items: [
      { path: '/datasets', label: 'Dataset Builder', icon: Database },
      { path: '/train', label: 'Training Console', icon: Sliders },
      { path: '/models', label: 'Models Comparison', icon: BarChart2 },
      { path: '/cross-arch', label: 'Cross-Architecture', icon: Cpu },
      { path: '/ablation', label: 'Ablation & Robustness', icon: ShieldCheck },
      { path: '/experiments', label: 'Experiments', icon: History },
    ]
  },
  {
    caption: 'OUTPUT',
    items: [
      { path: '/reports', label: 'Security Reports', icon: FileText },
    ]
  },
  {
    caption: 'DESIGN SYSTEM',
    items: [
      { path: '/foundations', label: 'Foundations', icon: BookOpen },
      { path: '/components', label: 'Components', icon: Code2 },
    ]
  }
];

export const AppLayout: React.FC = () => {
  const { theme, toggleTheme, sidebarCollapsed, toggleSidebar, activeJobId } = useAppStore();
  const location = useLocation();

  const [cmdOpen, setCmdOpen] = useState(false);
  const [toolchainPopoverOpen, setToolchainPopoverOpen] = useState(false);
  const [jobsPopoverOpen, setJobsPopoverOpen] = useState(false);

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  const { data: toolchain } = useQuery({
    queryKey: ['toolchain'],
    queryFn: fetchToolchainStatus,
    refetchInterval: 30000,
  });

  const { data: activeJob } = useQuery({
    queryKey: ['activeJob', activeJobId],
    queryFn: () => (activeJobId ? fetchJobStatus(activeJobId) : null),
    enabled: !!activeJobId,
    refetchInterval: 1500,
  });

  // Determine breadcrumb
  const currentPath = location.pathname;
  let breadcrumbTitle = 'Dashboard';
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (item.path === currentPath || (item.path !== '/' && currentPath.startsWith(item.path))) {
        breadcrumbTitle = `${group.caption} / ${item.label}`;
      }
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-base text-text-primary select-none">
      <CommandPalette isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />

      {/* Desktop / Tablet Sidebar (240px -> 56px icon rail) */}
      <aside 
        className={`hidden md:flex h-full bg-bg-surface border-r border-border-default flex-col justify-between transition-all duration-150 z-20 shrink-0 ${
          sidebarCollapsed ? 'w-14' : 'w-60'
        }`}
      >
        <div>
          {/* Top Brand Header */}
          <div className="h-12 border-b border-border-default flex items-center justify-between px-3">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-6 h-6 rounded-[4px] bg-bg-raised border border-border-default flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4 h-4 text-accent" strokeWidth={1.5} />
              </div>
              {!sidebarCollapsed && (
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono font-bold text-[13px] tracking-tight text-text-primary">CryptoScope</span>
                  <span className="font-mono text-[12px] text-text-disabled">v1.0.0</span>
                </div>
              )}
            </div>
            <button
              onClick={toggleSidebar}
              className="p-1.5 rounded-[4px] text-text-secondary hover:text-text-primary hover:bg-bg-raised transition cursor-pointer"
              title={sidebarCollapsed ? 'Expand sidebar (240px)' : 'Collapse sidebar (56px)'}
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" strokeWidth={1.5} /> : <ChevronLeft className="w-4 h-4" strokeWidth={1.5} />}
            </button>
          </div>

          {/* Grouped Navigation */}
          <nav className="p-2 space-y-4 overflow-y-auto max-h-[calc(100vh-140px)]">
            {NAV_GROUPS.map((group) => (
              <div key={group.caption} className="space-y-0.5">
                {!sidebarCollapsed && (
                  <div className="px-2.5 py-1 text-[12px] font-mono font-semibold uppercase tracking-[0.04em] text-text-disabled">
                    {group.caption}
                  </div>
                )}
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || 
                    (item.path !== '/' && location.pathname.startsWith(item.path));

                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-[4px] text-[12px] font-medium transition group ${
                        isActive
                          ? 'bg-bg-raised text-accent font-semibold border border-border-default'
                          : 'text-text-secondary hover:bg-bg-raised/60 hover:text-text-primary border border-transparent'
                      }`}
                      title={sidebarCollapsed ? item.label : undefined}
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-accent' : 'text-text-secondary group-hover:text-text-primary'}`} strokeWidth={1.5} />
                      {!sidebarCollapsed && <span>{item.label}</span>}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom Sidebar Footer */}
        <div className="p-2 border-t border-border-default bg-bg-surface text-[12px] font-mono space-y-1">
          <NavLink
            to="/settings"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-[4px] text-text-secondary hover:text-text-primary hover:bg-bg-raised transition"
            title="Settings"
          >
            <SettingsIcon className="w-4 h-4 shrink-0" strokeWidth={1.5} />
            {!sidebarCollapsed && <span>Settings</span>}
          </NavLink>

          {!sidebarCollapsed && (
            <div className="px-2.5 pt-1.5 border-t border-border-default flex items-center justify-between text-text-disabled text-[12px]">
              <span>FastAPI • ML</span>
              <span className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-status-success' : 'bg-status-danger'}`} />
                <span>Online</span>
              </span>
            </div>
          )}
        </div>
      </aside>

      {/* Main App Layout */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header Bar (48px) */}
        <header className="h-12 bg-bg-surface border-b border-border-default flex items-center justify-between px-4 sm:px-6 shrink-0 z-10">
          {/* Breadcrumb & Command Palette Trigger */}
          <div className="flex items-center gap-3">
            <span className="text-[12px] font-mono uppercase tracking-[0.04em] text-text-disabled">
              {breadcrumbTitle}
            </span>

            {/* ⌘K Global Search Trigger */}
            <button
              onClick={() => setCmdOpen(true)}
              className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 bg-bg-raised border border-border-default hover:border-border-strong rounded-[4px] text-[12px] text-text-secondary transition cursor-pointer"
              title="Open Command Palette (⌘K)"
            >
              <Search className="w-3.5 h-3.5 text-text-disabled" strokeWidth={1.5} />
              <span>Search commands / files...</span>
              <kbd className="px-1.5 py-0.5 rounded bg-bg-base border border-border-default text-[12px] font-mono">⌘K</kbd>
            </button>
          </div>

          {/* Right Status Indicators & Controls */}
          <div className="flex items-center gap-2.5">
            {/* Running Jobs Popover Indicator */}
            {activeJob && (
              <div className="relative">
                <button
                  onClick={() => setJobsPopoverOpen(!jobsPopoverOpen)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-bg-raised border border-border-default text-[12px] font-mono text-text-primary hover:border-accent cursor-pointer"
                >
                  <span className="w-2 h-2 rounded-full bg-accent animate-ping shrink-0" />
                  <span className="truncate max-w-[120px]">{activeJob.step}</span>
                  <span className="text-accent font-bold tabular-nums">{activeJob.progress}%</span>
                </button>

                {jobsPopoverOpen && (
                  <div className="absolute right-0 top-9 w-64 p-3 bg-bg-surface border border-border-default rounded-[6px] shadow-popover z-50 text-[12px] font-mono space-y-2">
                    <div className="flex justify-between items-center border-b border-border-default pb-1">
                      <span className="font-semibold text-text-primary uppercase text-[12px]">Active Background Job</span>
                      <span className="text-accent">{activeJob.job_id.slice(0, 8)}...</span>
                    </div>
                    <div className="text-text-secondary text-[12px]">{activeJob.message}</div>
                  </div>
                )}
              </div>
            )}

            {/* Toolchain Health Dot with Popover */}
            <div className="relative">
              <button
                onClick={() => setToolchainPopoverOpen(!toolchainPopoverOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-bg-raised border border-border-default text-[12px] font-mono text-text-secondary hover:text-text-primary transition cursor-pointer"
                title="Cross-Compiler Toolchain Health"
              >
                <span className={`w-2 h-2 rounded-full ${toolchain && toolchain.ready_isas.length > 0 ? 'bg-status-success' : 'bg-status-warning'}`} />
                <span>{toolchain ? `${toolchain.ready_isas.length}/5 ISAs` : 'Toolchain'}</span>
              </button>

              {toolchainPopoverOpen && (
                <div className="absolute right-0 top-9 w-72 p-3 bg-bg-surface border border-border-default rounded-[6px] shadow-popover z-50 text-[12px] font-mono space-y-2">
                  <div className="flex justify-between items-center border-b border-border-default pb-1">
                    <span className="font-semibold text-text-primary uppercase text-[12px]">Toolchain Matrix Status</span>
                    <span className="text-[12px] text-text-disabled">Host: {toolchain?.host_os}</span>
                  </div>
                  <div className="space-y-1">
                    {toolchain?.tools.map(t => (
                      <div key={t.name} className="flex items-center justify-between text-[12px]">
                        <span className="text-text-secondary truncate">{t.target_isa}</span>
                        <span className={`text-[12px] px-1.5 py-0.5 rounded-[4px] ${t.installed ? 'bg-status-success/15 text-status-success' : 'bg-status-warning/15 text-status-warning'}`}>
                          {t.installed ? 'Ready' : 'Synthetic Fallback'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-[4px] border border-border-default bg-bg-raised hover:bg-bg-surface text-text-secondary hover:text-text-primary transition cursor-pointer min-h-[32px] min-w-[32px] flex items-center justify-center"
              title="Toggle Dark/Light Mode"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-status-warning" strokeWidth={1.5} /> : <Moon className="w-4 h-4" strokeWidth={1.5} />}
            </button>
          </div>
        </header>

        {/* Scrollable Main Workspace Canvas (24px page margin, 24px gutters) */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-bg-base">
          <Outlet />
        </main>

        {/* Mobile Bottom Navigation Bar (>=44px touch targets) */}
        <div className="md:hidden h-14 bg-bg-surface border-t border-border-default flex items-center justify-around px-2 z-20 shrink-0">
          {[
            { path: '/', label: 'Dashboard', icon: Activity },
            { path: '/analyze', label: 'Analyze', icon: Terminal },
            { path: '/analyses', label: 'Results', icon: Layers },
            { path: '/reports', label: 'Reports', icon: FileText },
            { path: '/components', label: 'Design', icon: Code2 },
          ].map(item => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center min-w-[56px] min-h-[44px] text-[12px] font-mono transition ${
                  isActive ? 'text-accent font-semibold' : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                <Icon className="w-4 h-4 mb-0.5" strokeWidth={1.5} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>
    </div>
  );
};
