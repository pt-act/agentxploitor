"use client";

import { useState } from 'react';

interface VisualProof {
  id: string;
  findingId: string;
  beforeScreenshot: string;
  afterScreenshot: string;
  diffScreenshot?: string;
  timestamp: string;
  description: string;
}

interface VisualProofViewerProps {
  proofs: VisualProof[];
}

export default function VisualProofViewer({ proofs }: VisualProofViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'before' | 'after' | 'diff'>('side-by-side');

  if (!proofs || proofs.length === 0) {
    return (
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 text-center">
        <div className="text-4xl mb-3">📸</div>
        <div className="text-gray-400 text-sm">
          No visual proof screenshots captured for this audit.
        </div>
      </div>
    );
  }

  const current = proofs[currentIndex];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold text-lg">
          Visual Proof
          <span className="text-gray-500 font-normal text-base ml-2">
            ({currentIndex + 1} of {proofs.length})
          </span>
        </h3>

        {/* Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
            className="px-3 py-1.5 text-sm rounded border border-gray-700 text-gray-400 hover:border-gray-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Prev
          </button>
          <button
            onClick={() => setCurrentIndex(Math.min(proofs.length - 1, currentIndex + 1))}
            disabled={currentIndex === proofs.length - 1}
            className="px-3 py-1.5 text-sm rounded border border-gray-700 text-gray-400 hover:border-gray-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      </div>

      {/* Finding description */}
      <div className="bg-[#0a0e27] border border-gray-800 rounded-lg p-4">
        <div className="text-sm text-gray-400 mb-1">Captured for:</div>
        <div className="text-white font-medium">{current.description}</div>
        <div className="text-xs text-gray-500 mt-1">
          {new Date(current.timestamp).toLocaleString()}
        </div>
      </div>

      {/* View mode toggle */}
      <div className="flex gap-2">
        {(['side-by-side', 'before', 'after', 'diff'] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`px-3 py-1.5 text-sm rounded border transition-all ${
              viewMode === mode
                ? 'border-[#00ff41] bg-[#00ff41]/10 text-[#00ff41]'
                : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            {mode === 'side-by-side' ? 'Side by Side' : mode.charAt(0).toUpperCase() + mode.slice(1)}
          </button>
        ))}
      </div>

      {/* Screenshots */}
      {viewMode === 'side-by-side' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Before</div>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`data:image/png;base64,${current.beforeScreenshot}`}
                alt="Before"
                className="w-full h-auto"
              />
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-gray-500 uppercase tracking-wide">After</div>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`data:image/png;base64,${current.afterScreenshot}`}
                alt="After"
                className="w-full h-auto"
              />
            </div>
          </div>
        </div>
      )}

      {viewMode === 'before' && (
        <div className="border border-gray-800 rounded-lg overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/png;base64,${current.beforeScreenshot}`}
            alt="Before"
            className="w-full h-auto"
          />
        </div>
      )}

      {viewMode === 'after' && (
        <div className="border border-gray-800 rounded-lg overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/png;base64,${current.afterScreenshot}`}
            alt="After"
            className="w-full h-auto"
          />
        </div>
      )}

      {viewMode === 'diff' && (
        <div className="border border-gray-800 rounded-lg overflow-hidden">
          {current.diffScreenshot ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={`data:image/png;base64,${current.diffScreenshot}`}
              alt="Diff"
              className="w-full h-auto"
            />
          ) : (
            <div className="bg-[#1a1f3a] p-8 text-center text-gray-400">
              Diff not available — screenshots captured for different conditions
            </div>
          )}
        </div>
      )}

      {/* Proof navigation dots */}
      {proofs.length > 1 && (
        <div className="flex justify-center gap-2 pt-4">
          {proofs.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              className={`w-2 h-2 rounded-full transition-all ${
                idx === currentIndex
                  ? 'bg-[#00ff41] w-4'
                  : 'bg-gray-600 hover:bg-gray-500'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
