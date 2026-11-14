import React from 'react';
import { Leaf, Github, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <Leaf className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-white">CropGuard AI</span>
            </div>
            <p className="text-sm leading-relaxed">
              AI-powered plant disease detection using deep learning. Helping farmers identify
              crop diseases early and get treatment recommendations.
            </p>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-white font-semibold mb-4">Technology</h4>
            <ul className="space-y-2 text-sm">
              <li>EfficientNetB0 Deep Learning</li>
              <li>TensorFlow / Keras</li>
              <li>Flask REST API</li>
              <li>React + Tailwind CSS</li>
            </ul>
          </div>

          {/* Info */}
          <div>
            <h4 className="text-white font-semibold mb-4">About</h4>
            <ul className="space-y-2 text-sm">
              <li>38 Disease Classes</li>
              <li>14 Crop Species</li>
              <li>PlantVillage Dataset</li>
              <li>Pesticide Recommendations</li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm flex items-center gap-1">
            Made with <Heart className="w-3.5 h-3.5 text-red-400 fill-red-400" /> using AI &amp; Deep Learning
          </p>
          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} CropGuard AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
