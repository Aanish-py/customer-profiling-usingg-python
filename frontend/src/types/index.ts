// frontend/src/types/index.ts

export interface DatasetStatus {
  is_loaded: boolean;
  total_rows: number;
  unique_customers: number;
  unique_invoices: number;
  unique_products: number;
  date_start?: string;
  date_end?: string;
  file_exists_on_disk: boolean;
  file_size_mb: number;
}

export interface AuditStep {
  step: string;
  count: string | number;
  notes: string;
}

export interface AuditReport {
  steps: AuditStep[];
  raw_rows: number;
  duplicates_removed: number;
  missing_customer_id: number;
  invalid_price_rows: number;
  cancelled_invoices: number;
  final_rows: number;
  unique_customers: number;
}

export interface DataPreview {
  columns: string[];
  total_count: number;
  rows: Record<string, any>[];
}

export interface ExecutiveKPIs {
  total_revenue: number;
  unique_customers: number;
  total_orders: number;
  avg_order_value: number;
  cancellation_rate: number;
  unique_products: number;
  date_start: string;
  date_end: string;
}

export interface MonthlyPoint {
  month: string;
  revenue: number;
  orders: number;
}

export interface CategoryPoint {
  name: string;
  value: number;
  percentage?: number;
}

export interface OverviewCharts {
  monthly_trend: MonthlyPoint[];
  repeat_vs_onetime: CategoryPoint[];
  country_revenue: CategoryPoint[];
}

export interface DistributionBin {
  bin: string;
  count: number;
}

export interface Distributions {
  price_distribution: DistributionBin[];
  quantity_distribution: DistributionBin[];
  revenue_distribution: DistributionBin[];
}

export interface CustomerSearchItem {
  customer_id: number;
  frequency: number;
  monetary: number;
  recency: number;
  country: string;
}

export interface CustomerOrderItem {
  invoice_no: string;
  date: string;
  items_count: number;
  total_revenue: number;
}

export interface CustomerTopProduct {
  stock_code: string;
  description: string;
  total_qty: number;
  total_spend: number;
  order_count: number;
}

export interface ProductRecommendation {
  stock_code: string;
  description: string;
  score: number;
  reason: string;
}

export interface CustomerProfile {
  customer_id: number;
  country: string;
  first_purchase: string;
  last_purchase: string;
  frequency: number;
  monetary: number;
  avg_order_value: number;
  avg_qty_per_order: number;
  recency: number;
  tenure_days: number;
  repeat_rate: number;
  unique_products: number;
  inter_order_days?: number | null;
  order_history: CustomerOrderItem[];
  top_products: CustomerTopProduct[];
  predictions: {
    segment_name?: string | null;
    churn_probability?: number | null;
    churn_risk_level?: string | null;
    next_purchase_days?: number | null;
    next_purchase_date?: string | null;
    recommended_products: ProductRecommendation[];
  };
}

export interface CurvePoint {
  k: number;
  score: number;
}

export interface SegmentationCurves {
  elbow_curve: CurvePoint[];
  silhouette_curve: CurvePoint[];
  recommended_k: number;
}

export interface ClusterProfileItem {
  cluster: number;
  name: string;
  count: number;
  pct_customers: number;
  mean_recency: number;
  mean_frequency: number;
  mean_monetary: number;
  mean_aov: number;
  description: string;
}

export interface PCAPoint {
  customer_id: number;
  pca1: number;
  pca2: number;
  cluster: number;
  cluster_name: string;
  monetary: number;
  frequency: number;
  recency: number;
}

export interface SegmentationResult {
  n_clusters: number;
  silhouette_score: number;
  profiles: ClusterProfileItem[];
  pca_points: PCAPoint[];
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface NextPurchaseMetrics {
  is_trained: boolean;
  best_model_name: string;
  model_mae: number;
  model_rmse: number;
  model_r2: number;
  baseline_mae: number;
  mae_improvement_pct: number;
  sample_count: number;
  feature_importances: FeatureImportanceItem[];
  notes: string[];
}

export interface BatchNextPurchaseItem {
  customer_id: number;
  last_purchase_date: string;
  predicted_days: number;
  predicted_next_date: string;
  status: 'Overdue' | 'Due Soon' | 'On Track';
}

export interface ROCCurvePoint {
  fpr: number;
  tpr: number;
}

export interface ConfusionMatrixData {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  threshold: number;
}

export interface ChurnMetrics {
  is_trained: boolean;
  best_model_name: string;
  churn_rate: number;
  lr_auc: number;
  rf_auc: number;
  best_auc: number;
  baseline_auc: number;
  precision: number;
  recall: number;
  f1: number;
  train_size: number;
  test_size: number;
  roc_curve: ROCCurvePoint[];
  confusion_matrix: ConfusionMatrixData;
  feature_importances: FeatureImportanceItem[];
  notes: string[];
}

export interface AtRiskCustomerItem {
  customer_id: number;
  churn_probability: number;
  risk_level: string;
  recency_days: number;
  frequency: number;
  monetary: number;
  country: string;
}

export interface RecommendationEvaluation {
  is_built: boolean;
  hit_rate_at_n: number;
  mrr_at_n: number;
  catalog_size: number;
  test_customers_evaluated: number;
  top_n: number;
}

export interface AssociationRuleItem {
  antecedents: string[];
  consequents: string[];
  support: number;
  confidence: number;
  lift: number;
}

export interface PopularProductItem {
  stock_code: string;
  description: string;
  total_qty: number;
  order_count: number;
}

export interface ModelsSummary {
  dataset_ready: boolean;
  segmentation: {
    is_trained: boolean;
    n_clusters: number;
    silhouette: number;
    methodology: string;
  };
  next_purchase: {
    is_trained: boolean;
    best_model: string;
    model_mae: number;
    baseline_mae: number;
    mae_improvement_pct: number;
    methodology: string;
  };
  churn: {
    is_trained: boolean;
    best_model: string;
    roc_auc: number;
    churn_rate: number;
    methodology: string;
  };
  recommendations: {
    is_built: boolean;
    hit_rate_at_10: number;
    mrr_at_10: number;
    methodology: string;
  };
}
