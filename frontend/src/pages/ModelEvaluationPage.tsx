// frontend/src/pages/ModelEvaluationPage.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ShieldCheck, CheckCircle2, Target, CalendarClock, AlertTriangle, Lightbulb } from 'lucide-react';

import { getModelsSummary } from '@/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export const ModelEvaluationPage: React.FC = () => {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['models-summary'],
    queryFn: getModelsSummary,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Badge variant="primary" className="mb-2">Scientific Integrity & Verification</Badge>
        <h1 className="text-xl font-bold text-text">Model Evaluation & Benchmark Audit</h1>
        <p className="text-xs text-muted mt-0.5">
          Consolidated performance metrics, naive baseline comparisons, and anti-leakage safeguards.
        </p>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-muted">Loading models summary...</div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Models Consolidated Scorecard */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Segmentation Card */}
            <Card title="Segmentation" className="border-t-2 border-t-primary">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Algorithm:</span>
                  <span className="font-semibold text-text">K-Means + PCA</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Optimal Clusters (K):</span>
                  <span className="font-bold text-primary-light">{summary.segmentation.n_clusters}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Silhouette Score:</span>
                  <span className="font-mono text-emerald-400">{summary.segmentation.silhouette}</span>
                </div>
                <p className="text-[11px] text-muted pt-2 border-t border-border">
                  {summary.segmentation.methodology}
                </p>
              </div>
            </Card>

            {/* Next Purchase Card */}
            <Card title="Next Purchase" className="border-t-2 border-t-emerald-400">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Best Regressor:</span>
                  <span className="font-semibold text-text">{summary.next_purchase.best_model}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Model Test MAE:</span>
                  <span className="font-bold text-emerald-400">{summary.next_purchase.model_mae}d</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Baseline Dummy MAE:</span>
                  <span className="font-mono text-muted">{summary.next_purchase.baseline_mae}d</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Error Reduction:</span>
                  <Badge variant="success" size="sm">+{summary.next_purchase.mae_improvement_pct}%</Badge>
                </div>
                <p className="text-[11px] text-muted pt-2 border-t border-border">
                  {summary.next_purchase.methodology}
                </p>
              </div>
            </Card>

            {/* Churn Card */}
            <Card title="Churn Detection" className="border-t-2 border-t-rose-400">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Best Classifier:</span>
                  <span className="font-semibold text-text">{summary.churn.best_model}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Out-of-Time ROC-AUC:</span>
                  <span className="font-bold text-rose-400">{summary.churn.roc_auc}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Random Guess AUC:</span>
                  <span className="font-mono text-muted">0.500</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Churn Base Rate:</span>
                  <span className="text-text">{(summary.churn.churn_rate * 100).toFixed(1)}%</span>
                </div>
                <p className="text-[11px] text-muted pt-2 border-t border-border">
                  {summary.churn.methodology}
                </p>
              </div>
            </Card>

            {/* Recommendations Card */}
            <Card title="Recommendations" className="border-t-2 border-t-amber-400">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Strategy:</span>
                  <span className="font-semibold text-text">Hybrid Item-Item + Apriori</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Hit Rate@10:</span>
                  <span className="font-bold text-amber-400">
                    {(summary.recommendations.hit_rate_at_10 * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">MRR@10:</span>
                  <span className="font-mono text-primary-light">{summary.recommendations.mrr_at_10}</span>
                </div>
                <p className="text-[11px] text-muted pt-2 border-t border-border">
                  {summary.recommendations.methodology}
                </p>
              </div>
            </Card>
          </div>

          {/* Scientific Anti-Leakage Safeguards */}
          <Card
            title="Scientific Methodology & Data Leakage Prevention Guarantees"
            subtitle="Architectural measures implemented to prevent overoptimistic evaluation"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-surfaceHover border border-border">
                <div className="flex items-center gap-2 text-primary-light font-semibold text-xs mb-1">
                  <ShieldCheck className="w-4 h-4" />
                  Chronological Splits
                </div>
                <p className="text-[11px] text-muted leading-relaxed">
                  Random train/test splits cause future transaction leakage into the past. Churn and next-purchase
                  models strictly use historical observation cutoffs ($C$).
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surfaceHover border border-border">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs mb-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Cancellation Flag Isolation
                </div>
                <p className="text-[11px] text-muted leading-relaxed">
                  Cancelled invoices are explicitly flagged with <code>is_cancelled=True</code>. They are excluded
                  from purchase frequency and monetary counts while retained for net-revenue reconciliation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surfaceHover border border-border">
                <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs mb-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Realistic Baselines
                </div>
                <p className="text-[11px] text-muted leading-relaxed">
                  Every model is measured against naive statistical baselines (Dummy Regressor and Dummy Classifier)
                  to verify genuine machine learning predictive signal over random chance.
                </p>
              </div>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
};
