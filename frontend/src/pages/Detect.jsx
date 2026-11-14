import React, { useState, useCallback } from 'react';
import { ScanLine, RotateCcw, Loader2 } from 'lucide-react';
import ImageUpload from '../components/ImageUpload';
import PredictionResults from '../components/PredictionResults';
import ConfidenceChart from '../components/ConfidenceChart';

export default function Detect() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelect = useCallback((f) => {
    setFile(f);
    setResult(null);
    setError(null);
  }, []);

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', file);
      const res = await fetch('/api/predict', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Prediction failed. Please try again.');
      }
    } catch (err) {
      setError('Could not connect to the server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="page-container">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-4">
            <ScanLine className="w-4 h-4" />
            Disease Detection
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-800 mb-3">
            Detect Plant Disease
          </h1>
          <p className="text-slate-500 max-w-lg mx-auto">
            Upload a clear photo of the affected plant leaf for AI-powered disease identification.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Upload */}
          <div className="space-y-4">
            <ImageUpload onFileSelect={handleFileSelect} disabled={loading} />

            <div className="flex gap-3">
              <button
                onClick={handlePredict}
                disabled={!file || loading}
                className="btn-primary flex-1 justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <ScanLine className="w-5 h-5" />
                    Analyze Image
                  </>
                )}
              </button>

              {(result || error) && (
                <button onClick={handleReset} className="btn-secondary">
                  <RotateCcw className="w-5 h-5" />
                  Reset
                </button>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm animate-fade-in">
                {error}
              </div>
            )}
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {loading && (
              <div className="card p-12 flex flex-col items-center justify-center text-center animate-pulse-slow">
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
                <p className="font-semibold text-slate-700">Analyzing your image…</p>
                <p className="text-sm text-slate-500 mt-1">
                  Our AI is examining the leaf patterns
                </p>
              </div>
            )}

            {result && (
              <>
                <PredictionResults data={result} />
                <ConfidenceChart predictions={result.predictions} />
              </>
            )}

            {!result && !loading && !error && (
              <div className="card p-12 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                  <ScanLine className="w-8 h-8 text-gray-400" />
                </div>
                <p className="font-medium text-slate-500">Results will appear here</p>
                <p className="text-sm text-slate-400 mt-1">Upload an image and click Analyze</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
