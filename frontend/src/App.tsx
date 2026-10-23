import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppLayout } from '@/components/layout/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { AnalyzeFirmwarePage } from '@/pages/AnalyzeFirmwarePage';
import { AnalysesListPage } from '@/pages/AnalysesListPage';
import { AnalysisDetailPage } from '@/pages/AnalysisDetailPage';
import { FunctionDetailPage } from '@/pages/FunctionDetailPage';
import { ProtocolGraphPage } from '@/pages/ProtocolGraphPage';
import { DatasetBuilderPage } from '@/pages/DatasetBuilderPage';
import { TrainingConsolePage } from '@/pages/TrainingConsolePage';
import { ModelComparisonPage } from '@/pages/ModelComparisonPage';
import { CrossArchLabPage } from '@/pages/CrossArchLabPage';
import { AblationRobustnessPage } from '@/pages/AblationRobustnessPage';
import { ExperimentHistoryPage } from '@/pages/ExperimentHistoryPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { FoundationsPage } from '@/pages/FoundationsPage';
import { ComponentsPage } from '@/pages/ComponentsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="analyze" element={<AnalyzeFirmwarePage />} />
            <Route path="analyses" element={<AnalysesListPage />} />
            <Route path="analysis/:id" element={<AnalysisDetailPage />} />
            <Route path="functions/:id" element={<FunctionDetailPage />} />
            <Route path="protocol" element={<ProtocolGraphPage />} />
            <Route path="datasets" element={<DatasetBuilderPage />} />
            <Route path="train" element={<TrainingConsolePage />} />
            <Route path="models" element={<ModelComparisonPage />} />
            <Route path="cross-arch" element={<CrossArchLabPage />} />
            <Route path="ablation" element={<AblationRobustnessPage />} />
            <Route path="experiments" element={<ExperimentHistoryPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="foundations" element={<FoundationsPage />} />
            <Route path="components" element={<ComponentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
