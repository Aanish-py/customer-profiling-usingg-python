// frontend/src/pages/RecommendationsPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Lightbulb, Play, RefreshCw, Sparkles, TrendingUp, HelpCircle } from 'lucide-react';

import {
  getRecommendationEvaluation,
  buildRecommender,
  getCustomerRecommendations,
  getAssociationRules,
  getPopularProducts,
  searchCustomers,
} from '@/api';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';

export const RecommendationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [targetCustomerId, setTargetCustomerId] = useState<number>(14646);
  const [topN, setTopN] = useState<number>(5);

  const { data: evaluation, isLoading } = useQuery({
    queryKey: ['recommendation-evaluation'],
    queryFn: getRecommendationEvaluation,
  });

  const { data: rules } = useQuery({
    queryKey: ['association-rules'],
    queryFn: () => getAssociationRules(20),
  });

  const { data: popular } = useQuery({
    queryKey: ['popular-products'],
    queryFn: () => getPopularProducts(10),
  });

  const { data: customerRecs, isFetching: recsFetching } = useQuery({
    queryKey: ['customer-recommendations', targetCustomerId, topN],
    queryFn: () => getCustomerRecommendations(targetCustomerId, topN),
    enabled: !!targetCustomerId,
  });

  const { data: customerList } = useQuery({
    queryKey: ['rec-customer-list'],
    queryFn: () => searchCustomers('', 15),
  });

  const buildMutation = useMutation({
    mutationFn: () => buildRecommender(10),
    onSuccess: (data) => {
      queryClient.setQueryData(['recommendation-evaluation'], data);
      queryClient.invalidateQueries({ queryKey: ['customer-recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['association-rules'] });
      queryClient.invalidateQueries({ queryKey: ['popular-products'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Collaborative Filtering & Association</Badge>
          <h1 className="text-xl font-bold text-text">Product Recommendation Engine</h1>
          <p className="text-xs text-muted mt-0.5">
            Personalized item-to-item cosine similarity, market basket co-purchase rules, and cold-start fallback.
          </p>
        </div>

        <button
          onClick={() => buildMutation.mutate()}
          disabled={buildMutation.isPending}
          className="flex items-center gap-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-md shadow-primary/20 disabled:opacity-50"
        >
          {buildMutation.isPending ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 fill-current" />
          )}
          <span>{buildMutation.isPending ? 'Fitting Recommender...' : 'Re-Build Recommender'}</span>
        </button>
      </div>

      {/* Offline Evaluation Scorecard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Hit Rate@10"
          value={evaluation ? `${(evaluation.hit_rate_at_n * 100).toFixed(1)}%` : '...'}
          icon={Sparkles}
          iconColor="text-emerald-400"
          caption="Held-out last item in top 10"
        />
        <StatCard
          label="MRR@10"
          value={evaluation ? evaluation.mrr_at_n.toFixed(3) : '...'}
          icon={TrendingUp}
          iconColor="text-primary-light"
          caption="Mean Reciprocal Rank"
        />
        <StatCard
          label="Active SKU Catalog"
          value={evaluation ? evaluation.catalog_size.toLocaleString() : '...'}
          icon={Lightbulb}
          iconColor="text-amber-400"
          caption="Products in similarity matrix"
        />
        <StatCard
          label="Evaluation Sample"
          value={evaluation ? `${evaluation.test_customers_evaluated} users` : '...'}
          icon={HelpCircle}
          iconColor="text-indigo-400"
          caption="Tested on held-out purchases"
        />
      </div>

      {/* Customer Recommendation Explorer */}
      <Card
        title="Personalized Customer Recommendations"
        subtitle="Select any customer to generate real-time product recommendations with explanation reasons"
        action={
          <div className="flex items-center gap-2">
            <select
              value={targetCustomerId}
              onChange={(e) => setTargetCustomerId(Number(e.target.value))}
              className="bg-background border border-border rounded-lg px-2.5 py-1 text-xs text-text focus:outline-none focus:border-primary"
            >
              {customerList?.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  Customer #{c.customer_id} ({c.country})
                </option>
              ))}
            </select>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="bg-background border border-border rounded-lg px-2 py-1 text-xs text-text focus:outline-none focus:border-primary"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>
          </div>
        }
      >
        <div className="space-y-3 pt-2">
          {recsFetching ? (
            <div className="py-8 text-center text-xs text-muted">Scoring candidate products...</div>
          ) : customerRecs?.recommendations && customerRecs.recommendations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {customerRecs.recommendations.map((rec: any, i: number) => (
                <div
                  key={i}
                  className="p-4 rounded-xl bg-surfaceHover/80 border border-border flex items-start justify-between gap-3"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary-light flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                      #{i + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-text">{rec.description}</h4>
                      <span className="text-[10px] font-mono text-muted">SKU: {rec.stock_code}</span>
                      <p className="text-[11px] text-primary-light flex items-center gap-1 mt-1">
                        <Lightbulb className="w-3 h-3 text-amber-400 shrink-0" />
                        {rec.reason}
                      </p>
                    </div>
                  </div>
                  <Badge variant="primary" size="sm">Score {rec.score}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-muted">
              No recommendations available for this customer.
            </div>
          )}
        </div>
      </Card>

      {/* Association Rules & Global Popularity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Co-Purchase Association Rules */}
        <Card
          title="Market Basket Co-Purchase Rules"
          subtitle="Frequent itemsets: Antecedent &rarr; Consequent with Lift & Confidence"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                  <th className="py-2 px-3">If Bought (Antecedent)</th>
                  <th className="py-2 px-3">Also Buys (Consequent)</th>
                  <th className="py-2 px-3">Confidence</th>
                  <th className="py-2 px-3">Lift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {rules?.map((r, i) => (
                  <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                    <td className="py-2 px-3 font-medium text-text max-w-[150px] truncate">
                      {r.antecedents.join(', ')}
                    </td>
                    <td className="py-2 px-3 text-text max-w-[150px] truncate">
                      {r.consequents.join(', ')}
                    </td>
                    <td className="py-2 px-3 font-semibold text-primary-light">
                      {(r.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 px-3 font-mono text-emerald-400">{r.lift}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Global Popular Products */}
        <Card
          title="Global Popularity Fallback"
          subtitle="Top velocity products across the entire catalog for new buyers"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                  <th className="py-2 px-3">SKU</th>
                  <th className="py-2 px-3">Product Name</th>
                  <th className="py-2 px-3">Total Sold Units</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {popular?.map((p, i) => (
                  <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                    <td className="py-2 px-3 font-mono text-muted">{p.stock_code}</td>
                    <td className="py-2 px-3 text-text max-w-[200px] truncate">{p.description}</td>
                    <td className="py-2 px-3 font-semibold text-text">{p.total_qty.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
};
