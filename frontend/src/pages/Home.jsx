import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, Stethoscope, BarChart3, Leaf, Shield, Zap, ArrowRight } from 'lucide-react';

const features = [
  {
    icon: Upload,
    title: 'Upload & Detect',
    desc: 'Simply upload a photo of your plant leaf and our AI will identify the disease within seconds.',
    color: 'bg-primary-100 text-primary-600',
  },
  {
    icon: Stethoscope,
    title: 'Get Treatment',
    desc: 'Receive personalized pesticide and treatment recommendations based on the detected disease.',
    color: 'bg-amber-100 text-amber-600',
  },
  {
    icon: BarChart3,
    title: 'Track Crops',
    desc: 'Access a comprehensive library of 38 diseases across 14 crop species with detailed information.',
    color: 'bg-blue-100 text-blue-600',
  },
];

const stats = [
  { value: '38', label: 'Diseases Detected', icon: Shield },
  { value: '14', label: 'Crop Species', icon: Leaf },
  { value: '95%+', label: 'Accuracy', icon: Zap },
];

export default function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-emerald-800">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-primary-300 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-emerald-300 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 lg:py-40">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/15 backdrop-blur-sm rounded-full text-primary-100 text-sm font-medium mb-8">
              <Leaf className="w-4 h-4" />
              Powered by EfficientNetB0 Deep Learning
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white mb-6 leading-tight">
              🌿 CropGuard AI
            </h1>
            <p className="text-lg sm:text-xl text-primary-100 mb-10 leading-relaxed">
              AI-Powered Plant Disease Detection &amp; Treatment Recommendation.
              Protect your crops with state-of-the-art deep learning technology.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/detect"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-bold rounded-xl
                           hover:bg-primary-50 transition-all duration-200 shadow-xl shadow-black/10
                           hover:shadow-2xl hover:scale-[1.02] active:scale-[0.98] text-lg"
              >
                Start Detection
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/library"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 backdrop-blur-sm text-white font-semibold
                           rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-200 text-lg"
              >
                Browse Library
              </Link>
            </div>
          </div>
        </div>

        {/* Wave separator */}
        <div className="absolute bottom-0 inset-x-0">
          <svg viewBox="0 0 1440 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0 80H1440V30C1440 30 1320 0 1080 20C840 40 600 60 360 40C120 20 0 30 0 30V80Z"
              fill="#f9fafb"
            />
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section className="page-container py-16 sm:py-24">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-800 mb-4">How It Works</h2>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            Three simple steps to diagnose plant diseases and get treatment recommendations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <div
              key={i}
              className="card p-8 text-center hover:scale-[1.03] transition-transform duration-300"
            >
              <div className={`w-16 h-16 rounded-2xl ${f.color} flex items-center justify-center mx-auto mb-6`}>
                <f.icon className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3">{f.title}</h3>
              <p className="text-slate-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {stats.map((s, i) => (
              <div key={i} className="text-center group">
                <div className="w-14 h-14 rounded-2xl bg-primary-100 text-primary-600 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <s.icon className="w-7 h-7" />
                </div>
                <p className="text-4xl font-extrabold text-slate-800 mb-1">{s.value}</p>
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="page-container py-16 sm:py-24">
        <div className="bg-gradient-to-br from-primary-600 to-emerald-700 rounded-3xl p-10 sm:p-16 text-center text-white">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Ready to protect your crops?</h2>
          <p className="text-primary-100 text-lg mb-8 max-w-xl mx-auto">
            Upload a photo of your plant and get instant disease diagnosis with treatment recommendations.
          </p>
          <Link
            to="/detect"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-bold rounded-xl
                       hover:bg-primary-50 transition-all duration-200 shadow-xl text-lg
                       hover:scale-[1.02] active:scale-[0.98]"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
