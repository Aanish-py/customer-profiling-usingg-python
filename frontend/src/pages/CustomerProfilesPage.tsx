// frontend/src/pages/CustomerProfilesPage.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  User,
  Calendar,
  DollarSign,
  TrendingUp,
  Clock,
  Sparkles,
  AlertTriangle,
  Lightbulb,
  ShoppingBag,
} from 'lucide-react';

import { searchCustomers, getCustomerProfile } from '@/api';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';

export const CustomerProfilesPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCustomerId, setSelectedCustomerId] = useState<number>(14646);

  const { data: searchResults } = useQuery({
    queryKey: ['customer-search', searchQuery],
    queryFn: () => searchCustomers(searchQuery, 10),
  });

  const { data: profile, isLoading } = useQuery({
    queryKey: ['customer-profile', selectedCustomerId],
    queryFn: () => getCustomerProfile(selectedCustomerId),
    enabled: !!selectedCustomerId,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Individual Customer 360</Badge>
          <h1 className="text-xl font-bold text-text">Customer Profile Deep-Dive</h1>
          <p className="text-xs text-muted mt-0.5">
            Single-customer behavioral analytics, transaction timeline, and live machine learning signals.
          </p>
        </div>

        {/* Customer Search Selector */}
        <div className="flex items-center gap-2">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search Customer ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl pl-9 pr-3 py-2 text-xs text-text focus:outline-none focus:border-primary shadow-sm"
            />
          </div>
          {searchResults && searchResults.length > 0 && (
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
              className="bg-surface border border-border rounded-xl px-3 py-2 text-xs text-text focus:outline-none focus:border-primary shadow-sm"
            >
              {searchResults.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  Customer {c.customer_id} (£{c.monetary.toLocaleString()} · {c.country})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-xs text-muted">Loading customer 360 profile...</div>
      ) : profile ? (
        <div className="space-y-6">
          {/* Customer Summary Banner */}
          <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center text-white text-xl font-bold shadow-md shadow-primary/20">
                <User className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-text">Customer #{profile.customer_id}</h2>
                  <Badge variant="muted">{profile.country}</Badge>
                  {profile.repeat_rate === 1 ? (
                    <Badge variant="success">Repeat Buyer</Badge>
                  ) : (
                    <Badge variant="warning">One-Time Buyer</Badge>
                  )}
                </div>
                <p className="text-xs text-muted mt-1">
                  Active from 📅 {profile.first_purchase} &rarr; {profile.last_purchase} ({profile.tenure_days} days tenure)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {profile.predictions.segment_name && (
                <div className="text-right">
                  <span className="text-[10px] text-muted uppercase font-semibold">Assigned Segment</span>
                  <div className="text-xs font-semibold text-primary-light mt-0.5">
                    🎯 {profile.predictions.segment_name}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Predictive AI Signals Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Churn Risk */}
            <Card
              title="Churn Risk Evaluation"
              className={
                profile.predictions.churn_risk_level === 'High'
                  ? 'border-danger/40 bg-danger/5'
                  : 'border-border'
              }
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted">Predicted Churn Probability</div>
                  <div className="text-2xl font-bold text-text mt-1">
                    {profile.predictions.churn_probability !== null && profile.predictions.churn_probability !== undefined
                      ? `${(profile.predictions.churn_probability * 100).toFixed(1)}%`
                      : 'Unscored'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-surface border border-border">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Badge
                  variant={
                    profile.predictions.churn_risk_level === 'High'
                      ? 'danger'
                      : profile.predictions.churn_risk_level === 'Medium'
                      ? 'warning'
                      : 'success'
                  }
                >
                  {profile.predictions.churn_risk_level || 'Low Risk'}
                </Badge>
                <span className="text-[11px] text-muted">Based on recency & purchase dropoff</span>
              </div>
            </Card>

            {/* Next Purchase Estimate */}
            <Card title="Next Expected Purchase">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted">Predicted Timing</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">
                    {profile.predictions.next_purchase_days
                      ? `~${profile.predictions.next_purchase_days.toFixed(0)} days`
                      : 'N/A'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-surface border border-border">
                  <Calendar className="w-5 h-5 text-emerald-400" />
                </div>
              </div>
              <div className="mt-3 text-xs text-muted">
                Estimated Date:{' '}
                <strong className="text-text">{profile.predictions.next_purchase_date || 'N/A'}</strong>
              </div>
            </Card>

            {/* Cadence */}
            <Card title="Inter-Order Cadence">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted">Mean Gap Between Orders</div>
                  <div className="text-2xl font-bold text-text mt-1">
                    {profile.inter_order_days ? `${profile.inter_order_days.toFixed(1)} days` : 'Single order'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-surface border border-border">
                  <Clock className="w-5 h-5 text-primary-light" />
                </div>
              </div>
              <div className="mt-3 text-xs text-muted">
                Last ordered <strong className="text-text">{profile.recency} days ago</strong>
              </div>
            </Card>
          </div>

          {/* RFM Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Recency"
              value={`${profile.recency} days`}
              caption="Since last valid invoice"
            />
            <StatCard
              label="Frequency"
              value={`${profile.frequency} orders`}
              caption="Completed orders"
            />
            <StatCard
              label="Monetary Spend"
              value={`£${profile.monetary.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`}
              caption="Total lifetime revenue"
            />
            <StatCard
              label="Avg Order Value"
              value={`£${profile.avg_order_value.toFixed(2)}`}
              caption="Revenue per invoice"
            />
          </div>

          {/* Products & Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Purchased Products */}
            <Card title="Top Purchased Products" subtitle="Historical affinity based on order lines">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                      <th className="py-2.5 px-3">StockCode</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3">Qty</th>
                      <th className="py-2.5 px-3">Spend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {profile.top_products.slice(0, 6).map((p, i) => (
                      <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                        <td className="py-2 px-3 font-mono text-muted">{p.stock_code}</td>
                        <td className="py-2 px-3 text-text truncate max-w-xs">{p.description}</td>
                        <td className="py-2 px-3 text-text">{p.total_qty}</td>
                        <td className="py-2 px-3 font-semibold text-primary-light">£{p.total_spend.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* AI Product Recommendations */}
            <Card
              title="Tailored Product Recommendations"
              subtitle="Generated via Item-Item Collaborative Filtering & co-purchase rules"
            >
              <div className="space-y-3 pt-1">
                {profile.predictions.recommended_products.length > 0 ? (
                  profile.predictions.recommended_products.map((rec, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-surfaceHover/70 border border-border flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary-light flex items-center justify-center font-bold text-xs">
                          #{i + 1}
                        </div>
                        <div>
                          <h4 className="text-xs font-semibold text-text">{rec.description}</h4>
                          <span className="text-[11px] text-muted flex items-center gap-1 mt-0.5">
                            <Lightbulb className="w-3 h-3 text-amber-400" />
                            {rec.reason}
                          </span>
                        </div>
                      </div>
                      <Badge variant="primary" size="sm">Score {rec.score}</Badge>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-muted">
                    No recommendations trained yet. Train the recommender in the Recommendations module.
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Historical Order Timeline */}
          <Card title="Historical Invoice Timeline" subtitle="Complete invoice history for this customer">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 px-3">Invoice No</th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Items Count</th>
                    <th className="py-2.5 px-3">Total Spend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {profile.order_history.map((inv, i) => (
                    <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                      <td className="py-2 px-3 font-mono font-medium text-text">{inv.invoice_no}</td>
                      <td className="py-2 px-3 text-muted">{inv.date}</td>
                      <td className="py-2 px-3 text-text">{inv.items_count} items</td>
                      <td className="py-2 px-3 font-semibold text-primary-light">£{inv.total_revenue.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
};
