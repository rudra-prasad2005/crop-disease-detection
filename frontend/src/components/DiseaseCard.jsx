import React from 'react';
import { Leaf } from 'lucide-react';

const cropColors = {
  Apple: 'bg-red-100 text-red-700 border-red-200',
  Blueberry: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  Cherry: 'bg-pink-100 text-pink-700 border-pink-200',
  Corn: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  Grape: 'bg-purple-100 text-purple-700 border-purple-200',
  Orange: 'bg-orange-100 text-orange-700 border-orange-200',
  Peach: 'bg-rose-100 text-rose-700 border-rose-200',
  Pepper: 'bg-red-100 text-red-700 border-red-200',
  Potato: 'bg-amber-100 text-amber-700 border-amber-200',
  Raspberry: 'bg-pink-100 text-pink-700 border-pink-200',
  Soybean: 'bg-lime-100 text-lime-700 border-lime-200',
  Squash: 'bg-orange-100 text-orange-700 border-orange-200',
  Strawberry: 'bg-red-100 text-red-700 border-red-200',
  Tomato: 'bg-rose-100 text-rose-700 border-rose-200',
};

function getCropColor(crop) {
  return cropColors[crop] || 'bg-primary-100 text-primary-700 border-primary-200';
}

export default function DiseaseCard({ className: cls }) {
  const parts = cls.split('___');
  const crop = parts[0] || 'Unknown';
  const disease = parts[1] ? parts[1].replace(/_/g, ' ') : 'Unknown';
  const isHealthy = disease.toLowerCase() === 'healthy';
  const color = getCropColor(crop);

  return (
    <div className={`card p-4 border ${color.split(' ')[2]} hover:scale-[1.02] transition-transform duration-200`}>
      <div className="flex items-start gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${color.split(' ').slice(0, 2).join(' ')}`}>
          <Leaf className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-0.5">{crop}</p>
          <p className="text-sm font-semibold text-slate-800 leading-snug">
            {isHealthy ? (
              <span className="text-green-600">✓ Healthy</span>
            ) : (
              disease
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
