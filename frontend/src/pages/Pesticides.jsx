import React, { useState, useEffect, useMemo } from 'react';
import { FlaskConical, Search, Loader2, AlertCircle, ArrowUpDown } from 'lucide-react';

export default function Pesticides() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [filterCrop, setFilterCrop] = useState('All');
  const [filterIntensity, setFilterIntensity] = useState('All');
  const [sortField, setSortField] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);

  useEffect(() => {
    fetch('/api/pesticides')
      .then((r) => r.json())
      .then((d) => setData(d.pesticides || d || []))
      .catch(() => setError('Failed to load pesticide database.'))
      .finally(() => setLoading(false));
  }, []);

  const crops = useMemo(() => {
    const set = new Set(data.map((d) => d.crop));
    return ['All', ...Array.from(set).sort()];
  }, [data]);

  const intensities = useMemo(() => {
    const set = new Set(data.map((d) => d.intensity));
    return ['All', ...Array.from(set).sort()];
  }, [data]);

  const filtered = useMemo(() => {
    let result = data.filter((d) => {
      const matchSearch =
        search === '' ||
        Object.values(d).some((v) =>
          String(v).toLowerCase().includes(search.toLowerCase())
        );
      const matchCrop = filterCrop === 'All' || d.crop === filterCrop;
      const matchIntensity = filterIntensity === 'All' || d.intensity === filterIntensity;
      return matchSearch && matchCrop && matchIntensity;
    });

    if (sortField) {
      result = [...result].sort((a, b) => {
        const va = String(a[sortField]).toLowerCase();
        const vb = String(b[sortField]).toLowerCase();
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      });
    }

    return result;
  }, [data, search, filterCrop, filterIntensity, sortField, sortAsc]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const columns = [
    { key: 'crop', label: 'Crop' },
    { key: 'pest_type', label: 'Pest Type' },
    { key: 'intensity', label: 'Intensity' },
    { key: 'pesticide', label: 'Pesticide' },
  ];

  return (
    <div className="page-container">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-4">
            <FlaskConical className="w-4 h-4" />
            Pesticide Database
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-800 mb-3">
            Pesticide Database
          </h1>
          <p className="text-slate-500 max-w-lg mx-auto">
            Comprehensive pesticide recommendations for various crops and pest types.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search pesticides…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterCrop}
            onChange={(e) => setFilterCrop(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {crops.map((c) => (
              <option key={c} value={c}>{c === 'All' ? 'All Crops' : c}</option>
            ))}
          </select>
          <select
            value={filterIntensity}
            onChange={(e) => setFilterIntensity(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {intensities.map((i) => (
              <option key={i} value={i}>{i === 'All' ? 'All Intensities' : i}</option>
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
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {columns.map((col) => (
                      <th
                        key={col.key}
                        onClick={() => handleSort(col.key)}
                        className="text-left py-3 px-4 font-semibold text-slate-600 cursor-pointer hover:text-primary-700 select-none transition-colors"
                      >
                        <span className="inline-flex items-center gap-1.5">
                          {col.label}
                          <ArrowUpDown className="w-3.5 h-3.5 opacity-40" />
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-800">{row.crop}</td>
                      <td className="py-3 px-4 text-slate-600">{row.pest_type}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            row.intensity === 'high'
                              ? 'bg-red-100 text-red-700'
                              : row.intensity === 'medium'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-green-100 text-green-700'
                          }`}
                        >
                          {row.intensity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-700">{row.pesticide}</td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-12 text-center text-slate-400">
                        No pesticides match your filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-xs text-slate-500">
              Showing {filtered.length} of {data.length} records
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
