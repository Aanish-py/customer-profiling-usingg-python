// frontend/src/components/layout/Header.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getDatasetStatus } from '@/api';
import { Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

export const Header: React.FC = () => {
  const { data: status } = useQuery({
    queryKey: ['dataset-status'],
    queryFn: getDatasetStatus,
    refetchInterval: 15000,
  });

  return (
    <header className="h-16 border-b border-border bg-[#0D1117]/80 backdrop-blur-md sticky top-0 z-20 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold text-text">Customer Behavior Intelligence Platform</h2>
        <span className="text-xs text-muted/60">/</span>
        <span className="text-xs text-muted">Real-Time ML Decision Engine</span>
      </div>

      <div className="flex items-center gap-4">
        {status?.is_loaded ? (
          <div className="flex items-center gap-3 text-xs bg-surface border border-border px-3 py-1.5 rounded-lg shadow-sm">
            <div className="flex items-center gap-1.5 text-success">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span className="font-medium">Dataset Online</span>
            </div>
            <span className="text-border">|</span>
            <span className="text-muted">
              <strong className="text-text">{status.total_rows.toLocaleString()}</strong> rows
            </span>
            <span className="text-border">|</span>
            <span className="text-muted">
              <strong className="text-text">{status.unique_customers.toLocaleString()}</strong> customers
            </span>
          </div>
        ) : (
          <Badge variant="warning" className="flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            No Dataset Loaded
          </Badge>
        )}

        <div className="flex items-center gap-2">
          <Badge variant="primary" size="sm">
            v2.0 React
          </Badge>
        </div>
      </div>
    </header>
  );
};
