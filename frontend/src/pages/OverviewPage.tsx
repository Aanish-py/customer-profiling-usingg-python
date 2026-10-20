// frontend/src/pages/OverviewPage.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  DollarSign,
  Users,
  ShoppingBag,
  TrendingUp,
  Percent,
  Package,
  ArrowRight,
  Target,
  AlertTriangle,
  Lightbulb,
  CalendarClock,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';

import { getExecutiveKPIs, getOverviewCharts, getDatasetStatus } from '@/api';
import { StatCard } from '@/components/ui/StatCard';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

const DONUT_COLORS = ['#4F8EF7', '#8B949E'];

export const OverviewPage: React.FC = () => {
  const { data: status } = useQuery({ queryKey: ['dataset-status'], queryFn: getDatasetStatus });
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['executive-kpis'],
    queryFn: getExecutiveKPIs,
    enabled: !!status?.is_loaded,
  });
  const { data: charts, isLoading: chartsLoading } = useQuery({
    queryKey: ['overview-charts'],
    queryFn: getOverviewCharts,
    enabled: !!status?.is_loaded,
  });

  if (!status?.is_loaded) {
    return (
      <div className="py-12">
        <div className="bg-surface border border-border rounded-2xl p-8 max-w-2xl mx-auto text-center shadow-lg">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary-light mx-auto mb-4">
            <Package className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-text mb-2">No Dataset Loaded in Memory</h2>
          <p className="text-sm text-muted mb-6 leading-relaxed">
            The dataset is either being initialized or needs to be loaded. Go to Settings & Data to
            load the local UCI Online Retail file or configure custom options.
          </p>
          <Link
            to="/settings"
            className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-5 py-2.5 rounded-lg transition-all shadow-md shadow-primary/20"
          >
            <span>Open Settings & Data</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-surface via-[#131b26] to-surface border border-border rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Enterprise Retail Intelligence</Badge>
          <h1 className="text-2xl font-bold text-text tracking-tight">Executive Intelligence Overview</h1>
          <p className="text-xs text-muted mt-1">
            Real-time transaction insights, customer health metrics, and machine learning signals.
          </p>
        </div>
        {kpis && (
          <div className="text-right">
            <span className="text-[11px] text-muted uppercase font-semibold tracking-wider">Date Horizon</span>
            <div className="text-xs font-medium text-text bg-background border border-border px-3 py-1.5 rounded-lg mt-1">
              📅 {kpis.date_start} &rarr; {kpis.date_end}
            </div>
          </div>
        )}
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="Total Net Revenue"
          value={kpis ? `£${kpis.total_revenue.toLocaleString('en-GB', { maximumFractionDigits: 0 })}` : '...'}
          icon={DollarSign}
          iconColor="text-emerald-400"
          caption="Valid purchases only"
        />
        <StatCard
          label="Unique Customers"
          value={kpis ? kpis.unique_customers.toLocaleString() : '...'}
          icon={Users}
          iconColor="text-primary-light"
          caption="Identified buyers"
        />
        <StatCard
          label="Total Orders"
          value={kpis ? kpis.total_orders.toLocaleString() : '...'}
          icon={ShoppingBag}
          iconColor="text-indigo-400"
          caption="Distinct invoices"
        />
        <StatCard
          label="Avg Order Value"
          value={kpis ? `£${kpis.avg_order_value.toFixed(2)}` : '...'}
          icon={TrendingUp}
          iconColor="text-amber-400"
          caption="Per invoice spend"
        />
        <StatCard
          label="Cancel Rate"
          value={kpis ? `${kpis.cancellation_rate}%` : '...'}
          icon={Percent}
          iconColor="text-rose-400"
          caption="Invoice cancellation"
        />
        <StatCard
          label="Unique Products"
          value={kpis ? kpis.unique_products.toLocaleString() : '...'}
          icon={Package}
          iconColor="text-cyan-400"
          caption="Active catalog SKUs"
        />
      </div>

      {/* Primary Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Revenue Trend */}
        <Card
          title="Monthly Revenue Trajectory"
          subtitle="Net monthly spend across all customers (£)"
          className="lg:col-span-2"
        >
          <div className="h-72 w-full pt-4">
            {chartsLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-muted">Loading chart...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={charts?.monthly_trend || []}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4F8EF7" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4F8EF7" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                  <XAxis dataKey="month" stroke="#8B949E" fontSize={11} tickLine={false} />
                  <YAxis
                    stroke="#8B949E"
                    fontSize={11}
                    tickLine={false}
                    tickFormatter={(val) => `£${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D', borderRadius: '8px' }}
                    formatter={(val: any) => [`£${Number(val).toLocaleString()}`, 'Revenue']}
                  />
                  <Area type="monotone" dataKey="revenue" stroke="#4F8EF7" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Repeat vs One-time Buyers */}
        <Card title="Customer Retention Split" subtitle="One-time vs Repeat purchasers">
          <div className="h-72 w-full flex flex-col items-center justify-center">
            {chartsLoading ? (
              <div className="text-xs text-muted">Loading retention breakdown...</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={charts?.repeat_vs_onetime || []}
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {charts?.repeat_vs_onetime?.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={DONUT_COLORS[idx % DONUT_COLORS.length]} stroke="#161B22" />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D', borderRadius: '8px' }}
                      formatter={(val: any) => [`${Number(val).toLocaleString()} customers`, 'Count']}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-full space-y-2 mt-2 px-2">
                  {charts?.repeat_vs_onetime?.map((pt, i) => (
                    <div key={pt.name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: DONUT_COLORS[i] }} />
                        <span className="text-text">{pt.name}</span>
                      </div>
                      <span className="font-semibold text-text">{pt.percentage}%</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </Card>
      </div>

      {/* Top Countries Bar Chart & Quick Launch Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Top Geographies by Revenue" subtitle="Concentration of purchasing power by country" className="lg:col-span-2">
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts?.country_revenue || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" horizontal={false} />
                <XAxis type="number" stroke="#8B949E" fontSize={11} tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`} />
                <YAxis dataKey="name" type="category" stroke="#8B949E" fontSize={11} width={100} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D', borderRadius: '8px' }}
                  formatter={(val: any) => [`£${Number(val).toLocaleString()}`, 'Spend']}
                />
                <Bar dataKey="value" fill="#58A6FF" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Predictive Quick Launch */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-muted tracking-wider uppercase">Active AI Engines</h3>
          
          <Link
            to="/segmentation"
            className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-border hover:border-primary/40 hover:bg-surfaceHover transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary-light">
                <Target className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text group-hover:text-primary-light transition-colors">
                  K-Means Segmentation
                </h4>
                <p className="text-[11px] text-muted">RFM behavioral personas & 2D PCA</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted group-hover:translate-x-0.5 transition-transform" />
          </Link>

          <Link
            to="/next-purchase"
            className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-border hover:border-primary/40 hover:bg-surfaceHover transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <CalendarClock className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text group-hover:text-emerald-400 transition-colors">
                  Next-Purchase Timing
                </h4>
                <p className="text-[11px] text-muted">Days until next expected order</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted group-hover:translate-x-0.5 transition-transform" />
          </Link>

          <Link
            to="/churn"
            className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-border hover:border-danger/40 hover:bg-surfaceHover transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-danger/10 text-danger">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text group-hover:text-danger transition-colors">
                  Churn Risk Scoring
                </h4>
                <p className="text-[11px] text-muted">At-risk customer radar & ROC curve</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted group-hover:translate-x-0.5 transition-transform" />
          </Link>

          <Link
            to="/recommendations"
            className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-border hover:border-primary/40 hover:bg-surfaceHover transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Lightbulb className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text group-hover:text-amber-400 transition-colors">
                  Product Recommender
                </h4>
                <p className="text-[11px] text-muted">Item-Item CF & market basket rules</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-muted group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
};
