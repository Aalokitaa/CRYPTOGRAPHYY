import { create } from 'zustand';

interface AppState {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  activeJobId: string | null;
  setActiveJobId: (id: string | null) => void;
  selectedAnalysisId: string | null;
  setSelectedAnalysisId: (id: string | null) => void;
  selectedFunctionId: string | null;
  setSelectedFunctionId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'dark',
  toggleTheme: () => set((state) => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    if (next === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { theme: next };
  }),
  setTheme: (theme) => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ theme });
  },
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  activeJobId: null,
  setActiveJobId: (id) => set({ activeJobId: id }),
  selectedAnalysisId: null,
  setSelectedAnalysisId: (id) => set({ selectedAnalysisId: id }),
  selectedFunctionId: null,
  setSelectedFunctionId: (id) => set({ selectedFunctionId: id }),
}));
