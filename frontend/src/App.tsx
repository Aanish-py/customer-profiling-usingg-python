// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppLayout } from '@/components/layout/AppLayout';
import { OverviewPage } from '@/pages/OverviewPage';
import { DataExplorerPage } from '@/pages/DataExplorerPage';
import { CustomerProfilesPage } from '@/pages/CustomerProfilesPage';
import { SegmentationPage } from '@/pages/SegmentationPage';
import { NextPurchasePage } from '@/pages/NextPurchasePage';
import { ChurnAnalysisPage } from '@/pages/ChurnAnalysisPage';
import { RecommendationsPage } from '@/pages/RecommendationsPage';
import { ModelEvaluationPage } from '@/pages/ModelEvaluationPage';
import { SettingsPage } from '@/pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="explorer" element={<DataExplorerPage />} />
            <Route path="customers" element={<CustomerProfilesPage />} />
            <Route path="segmentation" element={<SegmentationPage />} />
            <Route path="next-purchase" element={<NextPurchasePage />} />
            <Route path="churn" element={<ChurnAnalysisPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="evaluation" element={<ModelEvaluationPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
