import React from 'react';

export default function ConfidenceChart({ predictions }) {
  if (!predictions || predictions.length === 0) return null;

  const maxConf = Math.max(...predictions.map((p) => p.confidence));

  const colors = [
    'from-primary-400 to-primary-600',
    'from-emerald-400 to-emerald-600',
    'from-teal-400 to-teal-600',
    'from-cyan-400 to-cyan-600',
    'from-green-400 to-green-600',
  ];

  return (
    <div className="card p-6">
      <h4 className="text-lg font-semibold text-slate-800 mb-4">Top Predictions</h4>
      <div className="space-y-3">
        {predictions.map((pred, idx) => {
          const pct = (pred.confidence * 100).toFixed(1);
          const label = pred.class.replace(/___/g, ' — ').replace(/_/g, ' ');
          return (
            <div key={idx}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-600 truncate pr-2 max-w-[70%]">
                  {label}
                </span>
                <span className="text-xs font-bold text-slate-700 flex-shrink-0">{pct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-2.5 rounded-full bg-gradient-to-r ${colors[idx % colors.length]} transition-all duration-1000 ease-out`}
                  style={{
                    width: `${(pred.confidence / maxConf) * 100}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
