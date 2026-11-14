import React, { useState, useEffect, useMemo } from 'react';
import { BookOpen, Search, Loader2, AlertCircle } from 'lucide-react';
import DiseaseCard from '../components/DiseaseCard';

export default function Library() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedCrop, setSelectedCrop] = useState('All');

  useEffect(() => {
    fetch('/api/classes')
      .then((r) => r.json())
      .then((data) => {
        setClasses(data.classes || data || []);
      })
      .catch(() => setError('Failed to load disease classes.'))
      .finally(() => setLoading(false));
  }, []);

  const crops = useMemo(() => {
    const set = new Set(classes.map((c) => c.split('___')[0]));
    return ['All', ...Array.from(set).sort()];
  }, [classes]);

  const filtered = useMemo(() => {
    return classes.filter((c) => {
      const matchSearch = c.toLowerCase().includes(search.toLowerCase());
      const matchCrop =
        selectedCrop === 'All' || c.split('___')[0] === selectedCrop;
      return matchSearch && matchCrop;
    });
  }, [classes, search, selectedCrop]);

  return (
    <div className="page-container">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-4">
            <BookOpen className="w-4 h-4" />
            Disease Library
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-800 mb-3">
            Disease Library
          </h1>
          <p className="text-slate-500 max-w-lg mx-auto">
            Browse all 38 plant diseases across 14 crop species in our database.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search diseases…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                         transition-shadow"
            />
          </div>
          <select
            value={selectedCrop}
            onChange={(e) => setSelectedCrop(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {crops.map((c) => (
              <option key={c} value={c}>
                {c === 'All' ? 'All Crops' : c}
              </option>
            ))}
          </select>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
            <p className="text-red-600 font-medium">{error}</p>
          </div>
        ) : (
          <>
            <p className="text-sm text-slate-500 mb-4">
              Showing {filtered.length} of {classes.length} diseases
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((cls) => (
                <DiseaseCard key={cls} className={cls} />
              ))}
            </div>
            {filtered.length === 0 && (
              <p className="text-center text-slate-400 py-12">No diseases match your search.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
