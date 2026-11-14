import React from 'react';
import { CheckCircle2, AlertTriangle, Leaf, Bug } from 'lucide-react';

export default function PredictionResults({ data }) {
  if (!data) return null;

  const { top_prediction, pesticide_info } = data;
  const isHealthy =
    top_prediction.disease.toLowerCase() === 'healthy' ||
    top_prediction.disease.toLowerCase().includes('healthy');

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Top Prediction Card */}
      <div
        className={`card p-6 border-l-4 ${
          isHealthy ? 'border-l-green-500' : 'border-l-amber-500'
        }`}
      >
        <div className="flex items-start gap-4">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
              isHealthy
                ? 'bg-green-100 text-green-600'
                : 'bg-amber-100 text-amber-600'
            }`}
          >
            {isHealthy ? (
              <CheckCircle2 className="w-6 h-6" />
            ) : (
              <AlertTriangle className="w-6 h-6" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-500 mb-1">Top Prediction</p>
            <h3 className="text-xl font-bold text-slate-800 mb-2">
              {top_prediction.disease.replace(/_/g, ' ')}
            </h3>
            <div className="flex items-center gap-2 mb-3">
              <Leaf className="w-4 h-4 text-primary-500" />
              <span className="text-sm font-medium text-primary-700">
                {top_prediction.crop}
              </span>
            </div>
            {/* Confidence bar */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-500">Confidence</span>
                <span className="text-sm font-bold text-slate-800">
                  {(top_prediction.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-3 rounded-full transition-all duration-1000 ease-out ${
                    isHealthy
                      ? 'bg-gradient-to-r from-green-400 to-green-600'
                      : 'bg-gradient-to-r from-amber-400 to-amber-600'
                  }`}
                  style={{ width: `${(top_prediction.confidence * 100).toFixed(1)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pesticide Recommendations */}
      {pesticide_info && pesticide_info.length > 0 && !isHealthy && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bug className="w-5 h-5 text-primary-600" />
            <h4 className="text-lg font-semibold text-slate-800">
              Treatment Recommendations
            </h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2.5 px-3 font-semibold text-slate-600">Pest Type</th>
                  <th className="text-left py-2.5 px-3 font-semibold text-slate-600">Intensity</th>
                  <th className="text-left py-2.5 px-3 font-semibold text-slate-600">Pesticide</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pesticide_info.map((p, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="py-2.5 px-3 text-slate-700">{p.pest_type}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          p.intensity === 'high'
                            ? 'bg-red-100 text-red-700'
                            : p.intensity === 'medium'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {p.intensity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 font-medium">{p.pesticide}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
