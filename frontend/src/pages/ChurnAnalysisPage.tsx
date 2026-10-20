// frontend/src/pages/ChurnAnalysisPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Play, RefreshCw, ShieldAlert, Download, Sliders, CheckCircle2 } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

import { getChurnMetrics, trainChurn, getAtRiskCustomers } from '@/api';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';

export const ChurnAnalysisPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [churnWindow, setChurnWindow] = useState<number>(90);
  const [threshold, setThreshold] = useState<number>(0.5);

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['churn-metrics'],
    queryFn: getChurnMetrics,
  });

  const { data: atRiskList } = useQuery({
    queryKey: ['at-risk-customers', threshold],
    queryFn: () => getAtRiskCustomers(threshold, 30),
    enabled: !!metrics?.is_trained,
  });

  const trainMutation = useMutation({
    mutationFn: (days: number) => trainChurn(days),
    onSuccess: (data) => {
      queryClient.setQueryData(['churn-metrics'], data);
      queryClient.invalidateQueries({ queryKey: ['at-risk-customers'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="danger" className="mb-2">Supervised Classification</Badge>
          <h1 className="text-xl font-bold text-text">Customer Churn Prediction & Risk Scoring</h1>
          <p className="text-xs text-muted mt-0.5">
            Identify customers likely to lapse using strictly separated historical observation windows.
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 bg-surface border border-border p-2 rounded-xl">
          <div className="flex items-center gap-2 px-2">
            <span className="text-xs text-muted font-medium">Churn Window:</span>
            <select
              value={churnWindow}
              onChange={(e) => setChurnWindow(Number(e.target.value))}
              className="bg-background border border-border rounded-lg px-2 py-1 text-xs text-text focus:outline-none focus:border-primary"
            >
              <option value={60}>60 days</option>
              <option value={90}>90 days (Standard)</option>
              <option value={120}>120 days</option>
              <option value={180}>180 days</option>
            </select>
          </div>

          <button
            onClick={() => trainMutation.mutate(churnWindow)}
            disabled={trainMutation.isPending}
            className="flex items-center gap-1.5 bg-danger hover:bg-rose-600 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-md shadow-danger/20 disabled:opacity-50"
          >
            {trainMutation.isPending ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>{trainMutation.isPending ? 'Training Model...' : 'Train Churn Model'}</span>
          </button>
        </div>
      </div>

      {/* Model Performance Scorecards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Best Classifier"
          value={metrics ? metrics.best_model_name : '...'}
          icon={ShieldAlert}
          iconColor="text-rose-400"
          caption="Compared via Out-of-Time AUC"
        />
        <StatCard
          label="ROC-AUC Score"
          value={metrics ? metrics.best_auc.toFixed(3) : '...'}
          icon={CheckCircle2}
          iconColor="text-emerald-400"
          caption="Baseline random guess = 0.500"
        />
        <StatCard
          label="Precision / Recall"
          value={metrics ? `${metrics.precision.toFixed(2)} / ${metrics.recall.toFixed(2)}` : '...'}
          icon={Sliders}
          iconColor="text-amber-400"
          caption={`F1-Score: ${metrics ? metrics.f1.toFixed(2) : '...'}`}
        />
        <StatCard
          label="Dataset Churn Rate"
          value={metrics ? `${(metrics.churn_rate * 100).toFixed(1)}%` : '...'}
          icon={AlertTriangle}
          iconColor="text-cyan-400"
          caption="Positive class distribution"
        />
      </div>

      {/* ROC Curve & Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ROC Curve */}
        <Card title="Receiver Operating Characteristic (ROC)" subtitle="True Positive Rate vs. False Positive Rate on test set">
          <div className="h-64 w-full pt-2">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-muted">Calculating ROC curve...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics?.roc_curve || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                  <XAxis dataKey="fpr" name="False Positive Rate" stroke="#8B949E" fontSize={10} tickLine={false} />
                  <YAxis dataKey="tpr" name="True Positive Rate" stroke="#8B949E" fontSize={10} tickLine={false} domain={[0, 1]} />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                  <Line type="monotone" dataKey="tpr" stroke="#F85149" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Confusion Matrix Card */}
        <Card title="Model Confusion Matrix" subtitle="True / False classification breakdowns">
          {metrics?.confusion_matrix && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto">
                <div className="p-4 rounded-xl bg-surfaceHover border border-border text-center">
                  <span className="text-[10px] text-muted uppercase font-semibold">True Negative (Retained)</span>
                  <div className="text-xl font-bold text-success mt-1">{metrics.confusion_matrix.tn}</div>
                </div>
                <div className="p-4 rounded-xl bg-surfaceHover border border-border text-center">
                  <span className="text-[10px] text-muted uppercase font-semibold">False Positive (False Alarm)</span>
                  <div className="text-xl font-bold text-amber-400 mt-1">{metrics.confusion_matrix.fp}</div>
                </div>
                <div className="p-4 rounded-xl bg-surfaceHover border border-border text-center">
                  <span className="text-[10px] text-muted uppercase font-semibold">False Negative (Missed Churn)</span>
                  <div className="text-xl font-bold text-danger mt-1">{metrics.confusion_matrix.fn}</div>
                </div>
                <div className="p-4 rounded-xl bg-surfaceHover border border-border text-center">
                  <span className="text-[10px] text-muted uppercase font-semibold">True Positive (Caught Churn)</span>
                  <div className="text-xl font-bold text-primary-light mt-1">{metrics.confusion_matrix.tp}</div>
                </div>
              </div>

              <div className="border-t border-border/80 pt-3 flex items-center justify-between text-xs text-muted">
                <span>Model evaluated on held-out out-of-time test set ({metrics.test_size} customers).</span>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* High-Risk Customer Watchlist Table */}
      <Card
        title="High-Risk Customer Churn Watchlist"
        subtitle="Customers exceeding the probability threshold, ranked by dropoff risk"
        action={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted">Threshold:</span>
              <input
                type="range"
                min="0.3"
                max="0.8"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-24 accent-danger"
              />
              <span className="font-semibold text-text w-10">{(threshold * 100).toFixed(0)}%</span>
            </div>
            <a
              href={`/api/predictions/churn/export-at-risk?threshold=${threshold}`}
              className="flex items-center gap-1.5 bg-surfaceHover hover:bg-border text-text text-xs font-medium px-3 py-1.5 rounded-lg border border-border transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export At-Risk CSV</span>
            </a>
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Customer ID</th>
                <th className="py-2.5 px-3">Churn Probability</th>
                <th className="py-2.5 px-3">Risk Tier</th>
                <th className="py-2.5 px-3">Recency</th>
                <th className="py-2.5 px-3">Historical Orders</th>
                <th className="py-2.5 px-3">Lifetime Spend</th>
                <th className="py-2.5 px-3">Country</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {atRiskList?.map((row, i) => (
                <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                  <td className="py-2 px-3 font-mono font-medium text-text">{row.customer_id}</td>
                  <td className="py-2 px-3 font-semibold text-danger">{(row.churn_probability * 100).toFixed(1)}%</td>
                  <td className="py-2 px-3">
                    <Badge variant={row.risk_level === 'High' ? 'danger' : 'warning'} size="sm">
                      {row.risk_level}
                    </Badge>
                  </td>
                  <td className="py-2 px-3 text-text">{row.recency_days} days</td>
                  <td className="py-2 px-3 text-text">{row.frequency} orders</td>
                  <td className="py-2 px-3 font-semibold text-primary-light">£{row.monetary.toLocaleString()}</td>
                  <td className="py-2 px-3 text-muted">{row.country}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
