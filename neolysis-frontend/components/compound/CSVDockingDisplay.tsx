'use client';

import { AffinityBar } from '@/components/ui/AffinityBar';

interface CSVDockingDisplayProps {
  docking: {
    affinity: number;
    ligand_eff: number;
    mw: number;
    logp: number;
    composite: number;
    confidence: number;
  };
  targetId?: string;
}

export function CSVDockingDisplay({ docking, targetId }: CSVDockingDisplayProps) {
  const { affinity, ligand_eff, mw, logp, composite, confidence } = docking;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Binding Affinity</h2>
        
        <div className="text-center mb-6">
          <div className={`text-5xl font-bold ${
            affinity < -8 ? 'text-green-600' : 
            affinity <= -5 ? 'text-yellow-600' : 'text-red-600'
          }`}>
            {affinity.toFixed(2)}
          </div>
          <p className="text-sm text-gray-500 mt-2">kcal/mol</p>
        </div>

        <AffinityBar affinity={affinity} />

        <div className="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div>
            <p className="text-xs text-gray-500">Composite Score</p>
            <p className="text-lg font-bold text-gray-900">{composite.toFixed(1)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Rank</p>
            <p className="text-lg font-bold text-gray-900">Top {(confidence * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Molecular Properties</h2>
        
        <div className="space-y-4">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Molecular Weight</span>
            <span className="font-bold text-gray-900">{mw.toFixed(1)} Da</span>
          </div>
          
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">LogP (Partition Coeff)</span>
            <span className="font-bold text-gray-900">{logp.toFixed(2)}</span>
          </div>
          
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Ligand Efficiency</span>
            <span className="font-bold text-gray-900">{ligand_eff.toFixed(3)}</span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Lipinski Rule of Five</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className={`px-3 py-2 rounded ${
              mw <= 500 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              MW ≤ 500: {mw <= 500 ? '✓' : '✗'}
            </div>
            <div className={`px-3 py-2 rounded ${
              logp <= 5 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              LogP ≤ 5: {logp <= 5 ? '✓' : '✗'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}