// frontend/src/pages/SettingsPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload,
  Database,
  Download,
  Play,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';

import {
  getDatasetStatus,
  loadDatasetFromDisk,
  downloadUciDataset,
  uploadDatasetFile,
  trainAllModels,
} from '@/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const { data: status } = useQuery({
    queryKey: ['dataset-status'],
    queryFn: getDatasetStatus,
  });

  const loadDiskMutation = useMutation({
    mutationFn: () => loadDatasetFromDisk(),
    onSuccess: (data: any) => {
      setMsg({ text: data.message || 'Dataset loaded successfully.', type: 'success' });
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      setMsg({ text: err.response?.data?.detail || 'Failed to load dataset.', type: 'error' });
    },
  });

  const downloadUciMutation = useMutation({
    mutationFn: downloadUciDataset,
    onSuccess: (data: any) => {
      setMsg({ text: `Downloaded ${data.size_mb} MB from UCI. Click "Load Dataset from Disk" now.`, type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['dataset-status'] });
    },
    onError: (err: any) => {
      setMsg({ text: err.response?.data?.detail || 'Failed to download dataset.', type: 'error' });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (f: File) => uploadDatasetFile(f),
    onSuccess: (data: any) => {
      setMsg({ text: data.message || 'File uploaded and processed.', type: 'success' });
      setFile(null);
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      setMsg({ text: err.response?.data?.detail || 'Upload failed.', type: 'error' });
    },
  });

  const trainAllMutation = useMutation({
    mutationFn: trainAllModels,
    onSuccess: (data: any) => {
      setMsg({ text: data.message || 'All models trained successfully.', type: 'success' });
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      setMsg({ text: err.response?.data?.detail || 'Training failed.', type: 'error' });
    },
  });

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <Badge variant="primary" className="mb-2">System Configuration</Badge>
        <h1 className="text-xl font-bold text-text">Dataset Management & Model Training</h1>
        <p className="text-xs text-muted mt-0.5">
          Configure dataset sources, ingest custom transaction files, and trigger end-to-end model training.
        </p>
      </div>

      {/* Status Feedback Toast */}
      {msg && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
            msg.type === 'success'
              ? 'bg-success/10 border-success/30 text-success'
              : 'bg-danger/10 border-danger/30 text-danger'
          }`}
        >
          <div className="flex items-center gap-2">
            {msg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>{msg.text}</span>
          </div>
          <button onClick={() => setMsg(null)} className="text-muted hover:text-text font-bold ml-4">
            &times;
          </button>
        </div>
      )}

      {/* Section 1: Ingestion Source */}
      <Card title="Dataset Ingestion" subtitle="Official UCI Online Retail (~24 MB) or custom transaction file">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Disk Source */}
            <div className="p-4 rounded-xl bg-surfaceHover border border-border flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-primary-light" />
                  <h4 className="text-xs font-semibold text-text">Local File (data/Online Retail.xlsx)</h4>
                </div>
                <p className="text-[11px] text-muted mt-1 leading-relaxed">
                  {status?.file_exists_on_disk
                    ? `Detected on disk (${status.file_size_mb} MB). Ready to load.`
                    : 'File not found on disk. Download it directly below.'}
                </p>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => loadDiskMutation.mutate()}
                  disabled={loadDiskMutation.isPending || !status?.file_exists_on_disk}
                  className="flex-1 bg-primary hover:bg-primary-hover text-white text-xs font-semibold py-2 px-3 rounded-lg transition-all shadow-md shadow-primary/20 disabled:opacity-40 flex items-center justify-center gap-1.5"
                >
                  {loadDiskMutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{loadDiskMutation.isPending ? 'Loading...' : 'Load from Disk'}</span>
                </button>

                {!status?.file_exists_on_disk && (
                  <button
                    onClick={() => downloadUciMutation.mutate()}
                    disabled={downloadUciMutation.isPending}
                    className="bg-surface border border-border hover:bg-border text-text text-xs py-2 px-3 rounded-lg flex items-center gap-1.5"
                  >
                    {downloadUciMutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    <Download className="w-3.5 h-3.5" />
                    <span>Download UCI</span>
                  </button>
                )}
              </div>
            </div>

            {/* Custom Upload Source */}
            <div className="p-4 rounded-xl bg-surfaceHover border border-border flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Upload className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-xs font-semibold text-text">Upload Custom File (.xlsx / .csv)</h4>
                </div>
                <p className="text-[11px] text-muted mt-1 leading-relaxed">
                  Upload an Excel or CSV file matching standard columns: InvoiceNo, StockCode, Quantity, etc.
                </p>
              </div>

              <div className="mt-4 space-y-2">
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="text-xs text-muted file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-hover cursor-pointer w-full"
                />
                {file && (
                  <button
                    onClick={() => file && uploadMutation.mutate(file)}
                    disabled={uploadMutation.isPending}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold py-2 px-3 rounded-lg transition-all flex items-center justify-center gap-1.5"
                  >
                    {uploadMutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    <span>{uploadMutation.isPending ? 'Processing...' : `Upload & Process ${file.name}`}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Section 2: One-Click Model Training */}
      <Card
        title="Automated Model Training Orchestrator"
        subtitle="Trains K-Means segmentation, next-purchase regression, churn classifier, and recommender sequentially"
      >
        <div className="space-y-4">
          <p className="text-xs text-muted leading-relaxed">
            Runs the full data science pipeline using the currently active in-memory clean dataset.
            Calculates Silhouette curves, out-of-time chronological train/test splits, ROC-AUC curves, and item similarity matrices.
          </p>

          <button
            onClick={() => trainAllMutation.mutate()}
            disabled={trainAllMutation.isPending || !status?.is_loaded}
            className="w-full bg-gradient-to-r from-primary via-indigo-600 to-primary hover:opacity-90 text-white text-xs font-bold py-3 px-4 rounded-xl transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2 disabled:opacity-40"
          >
            {trainAllMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            <span>{trainAllMutation.isPending ? 'Fitting All 4 Models in Background...' : '🚀 Train All Models (One-Click)'}</span>
          </button>
        </div>
      </Card>
    </div>
  );
};
