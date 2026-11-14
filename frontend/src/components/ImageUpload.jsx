import React, { useCallback, useState } from 'react';
import { Upload, Image as ImageIcon, X } from 'lucide-react';

export default function ImageUpload({ onFileSelect, disabled }) {
  const [preview, setPreview] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = useCallback(
    (file) => {
      if (!file || !file.type.startsWith('image/')) return;
      setPreview(URL.createObjectURL(file));
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    handleFile(file);
  };

  const clearPreview = () => {
    setPreview(null);
    onFileSelect(null);
  };

  return (
    <div className="w-full">
      {preview ? (
        <div className="relative group">
          <div className="rounded-2xl overflow-hidden border-2 border-primary-200 bg-white shadow-inner">
            <img
              src={preview}
              alt="Plant preview"
              className="w-full h-72 sm:h-80 object-contain bg-gray-50 p-2"
            />
          </div>
          <button
            onClick={clearPreview}
            disabled={disabled}
            className="absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md
                       hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
            aria-label="Remove image"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <label
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`flex flex-col items-center justify-center w-full h-72 sm:h-80 rounded-2xl border-2 border-dashed
                      cursor-pointer transition-all duration-300
                      ${
                        isDragOver
                          ? 'border-primary-400 bg-primary-50 scale-[1.02]'
                          : 'border-gray-300 bg-gray-50 hover:border-primary-300 hover:bg-primary-50/50'
                      }`}
        >
          <input
            type="file"
            accept="image/*"
            onChange={handleInputChange}
            className="hidden"
            disabled={disabled}
          />
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-colors ${
              isDragOver ? 'bg-primary-200 text-primary-700' : 'bg-primary-100 text-primary-600'
            }`}
          >
            {isDragOver ? (
              <ImageIcon className="w-8 h-8" />
            ) : (
              <Upload className="w-8 h-8" />
            )}
          </div>
          <p className="text-sm font-medium text-slate-700 mb-1">
            {isDragOver ? 'Drop your image here' : 'Drag & drop your plant image'}
          </p>
          <p className="text-xs text-slate-500">or click to browse • JPG, PNG, WebP</p>
        </label>
      )}
    </div>
  );
}
