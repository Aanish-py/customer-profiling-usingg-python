// frontend/src/api/index.ts
import { api } from './client';
import type {
  DatasetStatus,
  AuditReport,
  DataPreview,
  ExecutiveKPIs,
  OverviewCharts,
  Distributions,
  CustomerSearchItem,
  CustomerProfile,
  SegmentationCurves,
  SegmentationResult,
  NextPurchaseMetrics,
  BatchNextPurchaseItem,
  ChurnMetrics,
  AtRiskCustomerItem,
  RecommendationEvaluation,
  AssociationRuleItem,
  PopularProductItem,
  ModelsSummary,
} from '../types';

// ── Dataset ──
export const getDatasetStatus = async (): Promise<DatasetStatus> => {
  const { data } = await api.get<DatasetStatus>('/dataset/status');
  return data;
};

export const loadDatasetFromDisk = async (options = {}) => {
  const { data } = await api.post('/dataset/load-disk', options);
  return data;
};

export const downloadUciDataset = async () => {
  const { data } = await api.post('/dataset/download-uci');
  return data;
};

export const uploadDatasetFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getAuditReport = async (): Promise<AuditReport> => {
  const { data } = await api.get<AuditReport>('/dataset/audit-report');
  return data;
};

export const getDataPreview = async (kind: 'clean' | 'raw', page = 1, pageSize = 25): Promise<DataPreview> => {
  const { data } = await api.get<DataPreview>('/dataset/preview', {
    params: { kind, page, page_size: pageSize },
  });
  return data;
};

export const getCustomerFeatures = async (page = 1, pageSize = 25, search = ''): Promise<DataPreview> => {
  const { data } = await api.get<DataPreview>('/dataset/features', {
    params: { page, page_size: pageSize, search: search || undefined },
  });
  return data;
};

// ── Analytics ──
export const getExecutiveKPIs = async (): Promise<ExecutiveKPIs> => {
  const { data } = await api.get<ExecutiveKPIs>('/analytics/kpis');
  return data;
};

export const getOverviewCharts = async (): Promise<OverviewCharts> => {
  const { data } = await api.get<OverviewCharts>('/analytics/overview-charts');
  return data;
};

export const getDistributions = async (): Promise<Distributions> => {
  const { data } = await api.get<Distributions>('/analytics/distributions');
  return data;
};

// ── Customers ──
export const searchCustomers = async (q = '', limit = 20): Promise<CustomerSearchItem[]> => {
  const { data } = await api.get<CustomerSearchItem[]>('/customers/search', {
    params: { q, limit },
  });
  return data;
};

export const getCustomerProfile = async (customerId: number): Promise<CustomerProfile> => {
  const { data } = await api.get<CustomerProfile>(`/customers/${customerId}/profile`);
  return data;
};

// ── Segmentation ──
export const getSegmentationCurves = async (): Promise<SegmentationCurves> => {
  const { data } = await api.get<SegmentationCurves>('/segmentation/curves');
  return data;
};

export const trainSegmentation = async (nClusters?: number): Promise<SegmentationResult> => {
  const { data } = await api.post<SegmentationResult>('/segmentation/train', {
    n_clusters: nClusters || null,
  });
  return data;
};

export const getSegmentationResults = async (): Promise<SegmentationResult> => {
  const { data } = await api.get<SegmentationResult>('/segmentation/results');
  return data;
};

// ── Predictions (Next-Purchase & Churn) ──
export const trainNextPurchase = async (): Promise<NextPurchaseMetrics> => {
  const { data } = await api.post<NextPurchaseMetrics>('/predictions/next-purchase/train');
  return data;
};

export const getNextPurchaseMetrics = async (): Promise<NextPurchaseMetrics> => {
  const { data } = await api.get<NextPurchaseMetrics>('/predictions/next-purchase/metrics');
  return data;
};

export const estimateNextPurchase = async (customerId: number) => {
  const { data } = await api.post('/predictions/next-purchase/estimate', {
    customer_id: customerId,
  });
  return data;
};

export const getBatchNextPurchase = async (limit = 50): Promise<BatchNextPurchaseItem[]> => {
  const { data } = await api.get<BatchNextPurchaseItem[]>('/predictions/next-purchase/batch', {
    params: { limit },
  });
  return data;
};

export const trainChurn = async (churnWindowDays = 90): Promise<ChurnMetrics> => {
  const { data } = await api.post<ChurnMetrics>('/predictions/churn/train', {
    churn_window_days: churnWindowDays,
  });
  return data;
};

export const getChurnMetrics = async (): Promise<ChurnMetrics> => {
  const { data } = await api.get<ChurnMetrics>('/predictions/churn/metrics');
  return data;
};

export const getAtRiskCustomers = async (threshold = 0.5, limit = 50): Promise<AtRiskCustomerItem[]> => {
  const { data } = await api.get<AtRiskCustomerItem[]>('/predictions/churn/at-risk', {
    params: { threshold, limit },
  });
  return data;
};

// ── Recommendations ──
export const buildRecommender = async (topN = 10): Promise<RecommendationEvaluation> => {
  const { data } = await api.post<RecommendationEvaluation>('/recommendations/build', {
    top_n: topN,
  });
  return data;
};

export const getRecommendationEvaluation = async (): Promise<RecommendationEvaluation> => {
  const { data } = await api.get<RecommendationEvaluation>('/recommendations/evaluation');
  return data;
};

export const getCustomerRecommendations = async (customerId: number, topN = 5, excludePurchased = true) => {
  const { data } = await api.get(`/recommendations/customer/${customerId}`, {
    params: { top_n: topN, exclude_purchased: excludePurchased },
  });
  return data;
};

export const getAssociationRules = async (limit = 20): Promise<AssociationRuleItem[]> => {
  const { data } = await api.get<AssociationRuleItem[]>('/recommendations/rules', {
    params: { limit },
  });
  return data;
};

export const getPopularProducts = async (limit = 15): Promise<PopularProductItem[]> => {
  const { data } = await api.get<PopularProductItem[]>('/recommendations/top-products', {
    params: { limit },
  });
  return data;
};

// ── Models Summary ──
export const getModelsSummary = async (): Promise<ModelsSummary> => {
  const { data } = await api.get<ModelsSummary>('/models/summary');
  return data;
};

export const trainAllModels = async () => {
  const { data } = await api.post('/models/train-all');
  return data;
};
