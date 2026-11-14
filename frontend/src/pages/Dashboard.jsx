import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  CheckCircle2,
  XCircle,
  Cpu,
  Database,
  BarChart3,
  Loader2,
  AlertCircle,
} from 'lucide-react';

export default function Dashboard() {
  const [modelStatus, setModelStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/model-status').then((r) => r.json()),
      fetch('/api/stats').then((r) => r.json()),
    ])
      .then(([ms, st]) => {
        setModelStatus(ms);
        setStats(st);
      })
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container flex flex-col items-center justify-center py-32 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
        <p className="text-red-600 font-medium">{error}</p>
        <p className="text-sm text-slate-400 mt-1">Make sure the backend server is running.</p>
      </div>
    );
  }

  const trained = modelStatus?.model_exists || modelStatus?.trained;

  return (
    <div className="page-container">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-4">
            <LayoutDashboard className="w-4 h-4" />
            System Dashboard
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-800 mb-3">Dashboard</h1>
          <p className="text-slate-500">Monitor model status and performance metrics.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Model Status */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-primary-100 text-primary-600 rounded-xl flex items-center justify-center">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Model Status</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Status</span>
                {trained ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-green-700">
                    <CheckCircle2 className="w-4 h-4" />
                    Trained & Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-700">
                    <XCircle className="w-4 h-4" />
                    Not Trained
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Architecture</span>
                <span className="text-sm font-medium text-slate-700">
                  {modelStatus?.model_name || 'EfficientNetB0'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Classes</span>
                <span className="text-sm font-medium text-slate-700">
                  {modelStatus?.num_classes || 38}
                </span>
              </div>
              {modelStatus?.model_file && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Model File</span>
                  <span className="text-sm font-medium text-slate-700 truncate max-w-[50%]">
                    {modelStatus.model_file}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Dataset Info */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Dataset Overview</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Dataset</span>
                <span className="text-sm font-medium text-slate-700">
                  {stats?.dataset || 'PlantVillage'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Total Images</span>
                <span className="text-sm font-medium text-slate-700">
                  {stats?.total_images?.toLocaleString() || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Crop Species</span>
                <span className="text-sm font-medium text-slate-700">
                  {stats?.num_crops || 14}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Disease Classes</span>
                <span className="text-sm font-medium text-slate-700">
                  {stats?.num_classes || 38}
                </span>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="card p-6 md:col-span-2">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">Performance Metrics</h3>
            </div>

            {stats?.accuracy || stats?.metrics ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                {[
                  { label: 'Accuracy', value: stats.accuracy || stats.metrics?.accuracy },
                  { label: 'Precision', value: stats.precision || stats.metrics?.precision },
                  { label: 'Recall', value: stats.recall || stats.metrics?.recall },
                  { label: 'F1 Score', value: stats.f1_score || stats.metrics?.f1_score },
                ].map((m) => (
                  <div key={m.label} className="text-center">
                    <p className="text-3xl font-bold text-slate-800 mb-1">
                      {m.value != null
                        ? typeof m.value === 'number'
                          ? `${(m.value * (m.value <= 1 ? 100 : 1)).toFixed(1)}%`
                          : m.value
                        : '—'}
                    </p>
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                      {m.label}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-400">
                  {trained
                    ? 'Metrics will be available after evaluation.'
                    : 'Train the model to see performance metrics.'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
