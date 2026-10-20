// frontend/src/pages/NextPurchasePage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CalendarClock, Play, RefreshCw, BarChart3, CheckCircle2, AlertCircle } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

import {
  getNextPurchaseMetrics,
  trainNextPurchase,
  estimateNextPurchase,
  getBatchNextPurchase,
  searchCustomers,
} from '@/api';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';

export const NextPurchasePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [testCustomerId, setTestCustomerId] = useState<number>(14646);
  const [estimateResult, setEstimateResult] = useState<any>(null);

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['next-purchase-metrics'],
    queryFn: getNextPurchaseMetrics,
  });

  const { data: batchList } = useQuery({
    queryKey: ['batch-next-purchase'],
    queryFn: () => getBatchNextPurchase(25),
    enabled: !!metrics?.is_trained,
  });

  const { data: searchResults } = useQuery({
    queryKey: ['quick-customer-list'],
    queryFn: () => searchCustomers('', 15),
  });

  const trainMutation = useMutation({
    mutationFn: trainNextPurchase,
    onSuccess: (data) => {
      queryClient.setQueryData(['next-purchase-metrics'], data);
      queryClient.invalidateQueries({ queryKey: ['batch-next-purchase'] });
    },
  });

  const estimateMutation = useMutation({
    mutationFn: estimateNextPurchase,
    onSuccess: (data) => setEstimateResult(data),
    onError: (err: any) => {
      setEstimateResult({ error: err.response?.data?.detail || 'Failed to estimate.' });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Supervised Regression</Badge>
          <h1 className="text-xl font-bold text-text">Next-Purchase Timing Prediction</h1>
          <p className="text-xs text-muted mt-0.5">
            Predicts the exact number of days until a customer's next transaction using chronological inter-order history.
          </p>
        </div>

        <button
          onClick={() => trainMutation.mutate()}
          disabled={trainMutation.isPending}
          className="flex items-center gap-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-md shadow-primary/20 disabled:opacity-50"
        >
          {trainMutation.isPending ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 fill-current" />
          )}
          <span>{trainMutation.isPending ? 'Training Pipeline...' : 'Train Next-Purchase Model'}</span>
        </button>
      </div>

      {/* Model Scorecard Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Best Model"
          value={metrics ? metrics.best_model_name : '...'}
          icon={CalendarClock}
          iconColor="text-primary-light"
          caption="Selected via validation error"
        />
        <StatCard
          label="Model MAE"
          value={metrics ? `${metrics.model_mae} days` : '...'}
          icon={CheckCircle2}
          iconColor="text-emerald-400"
          caption="Mean Absolute Error on test set"
        />
        <StatCard
          label="Baseline Dummy MAE"
          value={metrics ? `${metrics.baseline_mae} days` : '...'}
          icon={AlertCircle}
          iconColor="text-amber-400"
          caption="Naive historical mean benchmark"
        />
        <StatCard
          label="Error Reduction"
          value={metrics ? `+${metrics.mae_improvement_pct}%` : '...'}
          icon={BarChart3}
          iconColor="text-indigo-400"
          caption="Accuracy gain over baseline"
        />
      </div>

      {/* Feature Importance & Individual Prediction */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feature Importance Bar Chart */}
        <Card
          title="Predictive Signal Importance"
          subtitle="Relative contribution of features to inter-order interval prediction"
        >
          <div className="h-64 w-full pt-2">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-muted">Loading model features...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metrics?.feature_importances || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" horizontal={false} />
                  <XAxis type="number" stroke="#8B949E" fontSize={10} tickLine={false} />
                  <YAxis dataKey="feature" type="category" stroke="#8B949E" fontSize={10} width={130} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                  <Bar dataKey="importance" fill="#4F8EF7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Single Customer Estimator Widget */}
        <Card title="Individual Customer Prediction Estimator" subtitle="Run live inference on any customer ID">
          <div className="space-y-4 pt-1">
            <div className="flex items-center gap-3">
              <select
                value={testCustomerId}
                onChange={(e) => setTestCustomerId(Number(e.target.value))}
                className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-xs text-text focus:outline-none focus:border-primary"
              >
                {searchResults?.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>
                    Customer {c.customer_id} (Orders: {c.frequency} · Recency: {c.recency}d)
                  </option>
                ))}
              </select>
              <button
                onClick={() => estimateMutation.mutate(testCustomerId)}
                disabled={estimateMutation.isPending}
                className="bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all shadow-md shadow-primary/20 disabled:opacity-50"
              >
                {estimateMutation.isPending ? 'Calculating...' : 'Predict Timing'}
              </button>
            </div>

            {estimateResult && (
              <div className="p-4 rounded-xl bg-surfaceHover border border-border space-y-2">
                {estimateResult.error ? (
                  <div className="text-xs text-danger">{estimateResult.error}</div>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted">Estimated Next Order:</span>
                      <span className="text-lg font-bold text-emerald-400">
                        ~{estimateResult.predicted_days} days
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted">Target Repurchase Date:</span>
                      <span className="font-semibold text-text">📅 {estimateResult.predicted_date}</span>
                    </div>
                    <p className="text-[11px] text-muted pt-1 border-t border-border/60">
                      {estimateResult.confidence_note}
                    </p>
                  </>
                )}
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Batch Predictions Table */}
      <Card
        title="Batch Customer Prediction Schedule"
        subtitle="Forward-looking schedule for automated marketing replenishment triggers"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Customer ID</th>
                <th className="py-2.5 px-3">Last Order Date</th>
                <th className="py-2.5 px-3">Predicted Gap (Days)</th>
                <th className="py-2.5 px-3">Estimated Target Date</th>
                <th className="py-2.5 px-3">Replenishment Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {batchList?.map((row, i) => (
                <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                  <td className="py-2 px-3 font-mono font-medium text-text">{row.customer_id}</td>
                  <td className="py-2 px-3 text-muted">{row.last_purchase_date}</td>
                  <td className="py-2 px-3 text-text">~{row.predicted_days} days</td>
                  <td className="py-2 px-3 font-semibold text-text">📅 {row.predicted_next_date}</td>
                  <td className="py-2 px-3">
                    <Badge
                      variant={
                        row.status === 'Overdue'
                          ? 'danger'
                          : row.status === 'Due Soon'
                          ? 'warning'
                          : 'success'
                      }
                      size="sm"
                    >
                      {row.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
