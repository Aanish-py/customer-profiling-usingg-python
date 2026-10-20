// frontend/src/pages/SegmentationPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Target, Download, Play, RefreshCw, BarChart2, Layers } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ScatterChart,
  Scatter,
  Cell,
} from 'recharts';

import { getSegmentationCurves, getSegmentationResults, trainSegmentation } from '@/api';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';

const CLUSTER_COLORS = ['#4F8EF7', '#3FB950', '#D29922', '#F85149', '#A371F7', '#388BFD', '#2EA043'];

export const SegmentationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedK, setSelectedK] = useState<number>(4);

  const { data: curves } = useQuery({
    queryKey: ['segmentation-curves'],
    queryFn: getSegmentationCurves,
  });

  const { data: results, isLoading } = useQuery({
    queryKey: ['segmentation-results'],
    queryFn: getSegmentationResults,
  });

  const trainMutation = useMutation({
    mutationFn: (k: number) => trainSegmentation(k),
    onSuccess: (data) => {
      queryClient.setQueryData(['segmentation-results'], data);
    },
  });

  const handleRetrain = () => {
    trainMutation.mutate(selectedK);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Unsupervised Learning</Badge>
          <h1 className="text-xl font-bold text-text">Customer Segmentation (K-Means)</h1>
          <p className="text-xs text-muted mt-0.5">
            Discover behavioral customer personas using log-transformed RFM features with PCA projection.
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 bg-surface border border-border p-2 rounded-xl">
          <div className="flex items-center gap-2 px-2">
            <span className="text-xs text-muted font-medium">Clusters (K):</span>
            <input
              type="number"
              min={2}
              max={8}
              value={selectedK}
              onChange={(e) => setSelectedK(Number(e.target.value))}
              className="w-14 bg-background border border-border rounded-lg px-2 py-1 text-xs text-text text-center focus:outline-none focus:border-primary"
            />
          </div>

          <button
            onClick={handleRetrain}
            disabled={trainMutation.isPending}
            className="flex items-center gap-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-md shadow-primary/20 disabled:opacity-50"
          >
            {trainMutation.isPending ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>{trainMutation.isPending ? 'Clustering...' : 'Run Segmentation'}</span>
          </button>

          <a
            href="/api/segmentation/export-clusters"
            className="flex items-center gap-1.5 bg-surfaceHover hover:bg-border text-text text-xs font-medium px-3 py-2 rounded-lg border border-border transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Model Overview Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Active Clusters (K)"
          value={results ? results.n_clusters : '...'}
          icon={Layers}
          iconColor="text-primary-light"
          caption="Discovered customer personas"
        />
        <StatCard
          label="Silhouette Score"
          value={results ? results.silhouette_score.toFixed(3) : '...'}
          icon={Target}
          iconColor="text-emerald-400"
          caption="Cluster separation quality (-1 to 1)"
        />
        <StatCard
          label="Recommended K"
          value={curves ? curves.recommended_k : '...'}
          icon={BarChart2}
          iconColor="text-amber-400"
          caption="Optimal via silhouette search"
        />
        <StatCard
          label="Customer Data Points"
          value={results ? results.pca_points.length.toLocaleString() : '...'}
          icon={Target}
          iconColor="text-indigo-400"
          caption="Projected in 2D space"
        />
      </div>

      {/* PCA 2D Scatter Chart */}
      <Card
        title="2D PCA Customer Projection"
        subtitle="Principal Component Analysis mapping multi-dimensional RFM features into 2D space"
      >
        <div className="h-80 w-full pt-2">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-xs text-muted">Calculating PCA projection...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                <XAxis dataKey="pca1" name="PCA Component 1" stroke="#8B949E" fontSize={10} tickLine={false} />
                <YAxis dataKey="pca2" name="PCA Component 2" stroke="#8B949E" fontSize={10} tickLine={false} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }) => {
                    if (!payload || !payload[0]) return null;
                    const data = payload[0].payload as any;
                    return (
                      <div className="bg-surface border border-border p-3 rounded-lg text-xs shadow-lg space-y-1">
                        <div className="font-bold text-text">Customer #{data.customer_id}</div>
                        <div className="text-primary-light font-medium">{data.cluster_name}</div>
                        <div className="text-muted">Spend: £{data.monetary.toLocaleString()}</div>
                        <div className="text-muted">Orders: {data.frequency} · Recency: {data.recency}d</div>
                      </div>
                    );
                  }}
                />
                <Scatter data={results?.pca_points || []}>
                  {results?.pca_points.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length]}
                      fillOpacity={0.7}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </div>
      </Card>

      {/* Cluster Profiles Table */}
      <Card title="Customer Persona Profiles & Behavioral Archetypes" subtitle="Mean metrics computed across each segment cluster">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Cluster</th>
                <th className="py-2.5 px-3">Segment Name</th>
                <th className="py-2.5 px-3">Customers</th>
                <th className="py-2.5 px-3">% of Base</th>
                <th className="py-2.5 px-3">Mean Recency</th>
                <th className="py-2.5 px-3">Mean Frequency</th>
                <th className="py-2.5 px-3">Mean Spend (£)</th>
                <th className="py-2.5 px-3">Mean AOV (£)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {results?.profiles.map((p, i) => (
                <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                  <td className="py-2.5 px-3">
                    <span
                      className="w-3 h-3 rounded-full inline-block mr-1 align-middle"
                      style={{ backgroundColor: CLUSTER_COLORS[p.cluster % CLUSTER_COLORS.length] }}
                    />
                    <span className="font-mono text-muted">#{p.cluster}</span>
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-text">{p.name}</td>
                  <td className="py-2.5 px-3 font-mono text-text">{p.count.toLocaleString()}</td>
                  <td className="py-2.5 px-3 font-medium text-primary-light">{p.pct_customers}%</td>
                  <td className="py-2.5 px-3 text-text">{p.mean_recency}d</td>
                  <td className="py-2.5 px-3 text-text">{p.mean_frequency} orders</td>
                  <td className="py-2.5 px-3 font-semibold text-emerald-400">£{p.mean_monetary.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-text">£{p.mean_aov.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* K Selection Diagnostics: Elbow & Silhouette */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Inertia Elbow Method" subtitle="Sum of squared distances (Inertia vs. K)">
          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curves?.elbow_curve || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                <XAxis dataKey="k" stroke="#8B949E" fontSize={10} tickLine={false} />
                <YAxis stroke="#8B949E" fontSize={10} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                <Line type="monotone" dataKey="score" stroke="#4F8EF7" strokeWidth={2} dot={{ fill: '#4F8EF7', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Silhouette Score Curve" subtitle="Cluster separation validation score across K">
          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curves?.silhouette_curve || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" />
                <XAxis dataKey="k" stroke="#8B949E" fontSize={10} tickLine={false} />
                <YAxis stroke="#8B949E" fontSize={10} tickLine={false} domain={[0, 0.6]} />
                <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                <Line type="monotone" dataKey="score" stroke="#3FB950" strokeWidth={2} dot={{ fill: '#3FB950', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
};
