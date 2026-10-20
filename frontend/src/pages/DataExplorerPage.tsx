// frontend/src/pages/DataExplorerPage.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Search, ChevronLeft, ChevronRight, Filter, BarChart3, Database } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

import { getAuditReport, getDataPreview, getCustomerFeatures, getDistributions } from '@/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export const DataExplorerPage: React.FC = () => {
  const [tab, setTab] = useState<'audit' | 'clean' | 'features' | 'distributions'>('audit');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data: audit } = useQuery({ queryKey: ['audit-report'], queryFn: getAuditReport });
  const { data: distributions } = useQuery({ queryKey: ['distributions'], queryFn: getDistributions });
  const { data: cleanPreview } = useQuery({
    queryKey: ['clean-preview', page],
    queryFn: () => getDataPreview('clean', page, 20),
    enabled: tab === 'clean',
  });
  const { data: features } = useQuery({
    queryKey: ['customer-features', page, search],
    queryFn: () => getCustomerFeatures(page, 20, search),
    enabled: tab === 'features',
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Badge variant="primary" className="mb-2">Data Quality & Ingestion</Badge>
          <h1 className="text-xl font-bold text-text">Exploratory Data Explorer</h1>
          <p className="text-xs text-muted mt-0.5">
            Audit preprocessing filters, view cleaned transaction records, and inspect RFM features.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1.5 bg-surface border border-border p-1 rounded-xl">
          <button
            onClick={() => setTab('audit')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'audit' ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-text'
            }`}
          >
            Audit Funnel
          </button>
          <button
            onClick={() => setTab('clean')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'clean' ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-text'
            }`}
          >
            Clean Transactions
          </button>
          <button
            onClick={() => setTab('features')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'features' ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-text'
            }`}
          >
            Customer Feature Matrix
          </button>
          <button
            onClick={() => setTab('distributions')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'distributions' ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-text'
            }`}
          >
            Distributions
          </button>
        </div>
      </div>

      {/* Tab: Audit Funnel */}
      {tab === 'audit' && audit && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <span className="text-[10px] font-semibold text-muted uppercase">Raw Rows Ingested</span>
              <div className="text-xl font-bold text-text mt-1">{audit.raw_rows.toLocaleString()}</div>
            </Card>
            <Card>
              <span className="text-[10px] font-semibold text-muted uppercase">Exact Duplicates Removed</span>
              <div className="text-xl font-bold text-amber-400 mt-1">{audit.duplicates_removed.toLocaleString()}</div>
            </Card>
            <Card>
              <span className="text-[10px] font-semibold text-muted uppercase">Missing CustomerIDs Dropped</span>
              <div className="text-xl font-bold text-rose-400 mt-1">{audit.missing_customer_id.toLocaleString()}</div>
            </Card>
            <Card>
              <span className="text-[10px] font-semibold text-muted uppercase">Final Clean Rows Retained</span>
              <div className="text-xl font-bold text-success mt-1">{audit.final_rows.toLocaleString()}</div>
            </Card>
          </div>

          <Card title="Step-by-Step Data Preprocessing Pipeline Audit">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 px-3">Pipeline Step</th>
                    <th className="py-2.5 px-3">Metric / Count</th>
                    <th className="py-2.5 px-3">Filter Notes & Reasoning</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {audit.steps.map((s, i) => (
                    <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-text">{s.step}</td>
                      <td className="py-2.5 px-3 font-mono text-primary-light">{s.count}</td>
                      <td className="py-2.5 px-3 text-muted">{s.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab: Clean Transactions Table */}
      {tab === 'clean' && (
        <Card
          title="Clean Transaction Records"
          subtitle={`Showing page ${page} of ~${Math.ceil((cleanPreview?.total_count || 1) / 20)}`}
          action={
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-border bg-surfaceHover text-muted hover:text-text disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-text px-2">Page {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded-lg border border-border bg-surfaceHover text-muted hover:text-text"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-3">Invoice</th>
                  <th className="py-2.5 px-3">StockCode</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3">Qty</th>
                  <th className="py-2.5 px-3">UnitPrice</th>
                  <th className="py-2.5 px-3">Revenue</th>
                  <th className="py-2.5 px-3">CustomerID</th>
                  <th className="py-2.5 px-3">Country</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {cleanPreview?.rows.map((row, i) => (
                  <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                    <td className="py-2 px-3 font-mono text-text">{row.InvoiceNo}</td>
                    <td className="py-2 px-3 font-mono text-muted">{row.StockCode}</td>
                    <td className="py-2 px-3 text-text max-w-xs truncate">{row.Description}</td>
                    <td className="py-2 px-3 text-text">{row.Quantity}</td>
                    <td className="py-2 px-3 text-text">£{Number(row.UnitPrice).toFixed(2)}</td>
                    <td className="py-2 px-3 font-semibold text-primary-light">£{Number(row.Revenue).toFixed(2)}</td>
                    <td className="py-2 px-3 font-mono text-text">{row.CustomerID}</td>
                    <td className="py-2 px-3 text-muted">{row.Country}</td>
                    <td className="py-2 px-3">
                      {row.is_cancelled ? (
                        <Badge variant="danger" size="sm">Cancelled</Badge>
                      ) : (
                        <Badge variant="success" size="sm">Purchase</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab: Customer Feature Matrix */}
      {tab === 'features' && (
        <Card
          title="Engineered Customer Feature Matrix"
          subtitle="One row per customer with aggregated RFM, order gap, and tenure attributes"
          action={
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-muted absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Search Customer ID..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="bg-background border border-border rounded-lg pl-8 pr-3 py-1 text-xs text-text focus:outline-none focus:border-primary"
                />
              </div>
              <a
                href="/api/dataset/export-features"
                className="flex items-center gap-1.5 bg-surfaceHover hover:bg-border text-text text-xs px-3 py-1.5 rounded-lg border border-border transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </a>
            </div>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-3">Customer ID</th>
                  <th className="py-2.5 px-3">Frequency</th>
                  <th className="py-2.5 px-3">Monetary</th>
                  <th className="py-2.5 px-3">AOV</th>
                  <th className="py-2.5 px-3">Recency (Days)</th>
                  <th className="py-2.5 px-3">Tenure (Days)</th>
                  <th className="py-2.5 px-3">Repeat Buyer</th>
                  <th className="py-2.5 px-3">Inter-Order Gap</th>
                  <th className="py-2.5 px-3">Country</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {features?.rows.map((row, i) => (
                  <tr key={i} className="hover:bg-surfaceHover/50 transition-colors">
                    <td className="py-2 px-3 font-mono font-medium text-text">{row.CustomerID}</td>
                    <td className="py-2 px-3 text-text">{row.frequency} orders</td>
                    <td className="py-2 px-3 font-semibold text-primary-light">£{Number(row.monetary).toFixed(2)}</td>
                    <td className="py-2 px-3 text-text">£{Number(row.avg_order_value).toFixed(2)}</td>
                    <td className="py-2 px-3 text-text">{row.recency}d</td>
                    <td className="py-2 px-3 text-muted">{row.tenure_days}d</td>
                    <td className="py-2 px-3">
                      {row.repeat_rate === 1 ? (
                        <Badge variant="primary" size="sm">Repeat</Badge>
                      ) : (
                        <Badge variant="muted" size="sm">One-Time</Badge>
                      )}
                    </td>
                    <td className="py-2 px-3 text-muted">
                      {row.inter_order_days ? `${Number(row.inter_order_days).toFixed(1)}d` : 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-muted">{row.country}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-border mt-4 pt-3">
            <span className="text-xs text-muted">
              Showing page {page} of ~{Math.ceil((features?.total_count || 1) / 20)}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-border bg-surfaceHover text-muted hover:text-text disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded-lg border border-border bg-surfaceHover text-muted hover:text-text"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Tab: Distributions */}
      {tab === 'distributions' && distributions && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Unit Price Distribution" subtitle="Histogram of item prices (£0–£20)">
            <div className="h-60 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributions.price_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                  <XAxis dataKey="bin" stroke="#8B949E" fontSize={9} interval={0} angle={-30} textAnchor="end" height={45} />
                  <YAxis stroke="#8B949E" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                  <Bar dataKey="count" fill="#4F8EF7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Order Quantity Distribution" subtitle="Items per transaction line (1–100)">
            <div className="h-60 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributions.quantity_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                  <XAxis dataKey="bin" stroke="#8B949E" fontSize={9} interval={0} angle={-30} textAnchor="end" height={45} />
                  <YAxis stroke="#8B949E" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                  <Bar dataKey="count" fill="#58A6FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Order Revenue Distribution" subtitle="Net spend per invoice (£0–£1,000)">
            <div className="h-60 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributions.revenue_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                  <XAxis dataKey="bin" stroke="#8B949E" fontSize={9} interval={0} angle={-30} textAnchor="end" height={45} />
                  <YAxis stroke="#8B949E" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', borderColor: '#21262D' }} />
                  <Bar dataKey="count" fill="#3FB950" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
