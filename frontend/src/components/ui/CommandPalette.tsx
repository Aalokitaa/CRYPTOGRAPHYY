import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Terminal, 
  Layers, 
  Network, 
  Database, 
  Sliders, 
  BarChart2, 
  Cpu, 
  ShieldCheck, 
  History, 
  FileText, 
  Settings, 
  BookOpen, 
  Code2 
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const COMMANDS = [
  { label: 'Dashboard', path: '/', category: 'Analysis', icon: Layers },
  { label: 'Analyze Firmware', path: '/analyze', category: 'Analysis', icon: Terminal },
  { label: 'Recent Analyses', path: '/analyses', category: 'Analysis', icon: Layers },
  { label: 'Protocol Graph', path: '/protocol', category: 'Analysis', icon: Network },
  { label: 'Dataset Builder', path: '/datasets', category: 'Research', icon: Database },
  { label: 'Training Console', path: '/train', category: 'Research', icon: Sliders },
  { label: 'Model Comparison', path: '/models', category: 'Research', icon: BarChart2 },
  { label: 'Cross-Architecture Lab', path: '/cross-arch', category: 'Research', icon: Cpu },
  { label: 'Ablation & Robustness', path: '/ablation', category: 'Research', icon: ShieldCheck },
  { label: 'Experiment History', path: '/experiments', category: 'Research', icon: History },
  { label: 'Security Reports', path: '/reports', category: 'Output', icon: FileText },
  { label: 'Foundations (Design System)', path: '/foundations', category: 'Design', icon: BookOpen },
  { label: 'Components Catalog', path: '/components', category: 'Design', icon: Code2 },
  { label: 'Settings', path: '/settings', category: 'System', icon: Settings },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filtered = COMMANDS.filter(cmd => 
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/60 backdrop-blur-none">
      <div 
        className="w-full max-w-lg bg-bg-surface border border-border-default rounded-[6px] shadow-popover overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-3 border-b border-border-default h-11">
          <Search className="w-4 h-4 text-text-secondary mr-2 shrink-0" strokeWidth={1.5} />
          <input
            type="text"
            autoFocus
            placeholder="Type a command or jump to screen..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-[13px] text-text-primary placeholder:text-text-disabled outline-none font-sans"
          />
          <kbd className="px-1.5 py-0.5 rounded-[4px] bg-bg-raised border border-border-default text-[12px] font-mono text-text-secondary select-none">
            ESC
          </kbd>
        </div>

        {/* Command list */}
        <div className="max-h-72 overflow-y-auto p-1.5 space-y-0.5">
          {filtered.length === 0 ? (
            <div className="p-4 text-center text-[12px] text-text-disabled font-mono">
              No matching commands or routes.
            </div>
          ) : (
            filtered.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.path}
                  onClick={() => handleSelect(cmd.path)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-[4px] hover:bg-bg-raised text-left transition-colors text-[12px] group cursor-pointer min-h-[44px]"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4 text-text-secondary group-hover:text-accent" strokeWidth={1.5} />
                    <span className="text-text-primary font-medium">{cmd.label}</span>
                  </div>
                  <span className="text-[12px] font-mono uppercase tracking-wider text-text-disabled">
                    {cmd.category}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
