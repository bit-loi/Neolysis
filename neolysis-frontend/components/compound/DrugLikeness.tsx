import { Compound } from '@/lib/types';
import { Check, X } from 'lucide-react';

interface DrugLikenessProps {
  compound: Compound;
}

export function DrugLikeness({ compound }: DrugLikenessProps) {
  const rules = [
    { name: 'Molecular Weight', value: compound.mw, threshold: 500, unit: 'g/mol' },
    { name: 'LogP', value: compound.logP, threshold: 5, unit: '' },
    { name: 'Hydrogen Bond Donors', value: compound.hbd, threshold: 5, unit: '' },
    { name: 'Hydrogen Bond Acceptors', value: compound.hba, threshold: 10, unit: '' },
  ];

  const passedCount = rules.filter((r) => r.value <= r.threshold).length;
  const veberRules = [
    { name: 'TPSA', value: compound.tpsa, threshold: 140, unit: 'Å²' },
    { name: 'Rotatable Bonds', value: compound.rotBonds, threshold: 10, unit: '' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Drug Likeness</h2>

      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          {compound.lipinskiPass ? (
            <>
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="font-semibold text-emerald-700">Passes Lipinski Rule of 5</p>
                <p className="text-sm text-gray-500">{passedCount}/4 rules passed</p>
              </div>
            </>
          ) : (
            <>
              <div className="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center">
                <X className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <p className="font-semibold text-rose-700">Fails Lipinski Rule of 5</p>
                <p className="text-sm text-gray-500">{passedCount}/4 rules passed</p>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-700">Lipinski Rule of 5</h3>
        {rules.map((rule) => {
          const passes = rule.value <= rule.threshold;
          return (
            <div
              key={rule.name}
              className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
            >
              <div className="flex items-center gap-2">
                {passes ? (
                  <Check className="w-4 h-4 text-emerald-500" />
                ) : (
                  <X className="w-4 h-4 text-rose-500" />
                )}
                <span className="text-sm text-gray-600">{rule.name}</span>
              </div>
              <div className="text-right">
                <span className={`text-sm font-medium ${passes ? 'text-gray-900' : 'text-rose-600'}`}>
                  {rule.value.toFixed(rule.unit === 'g/mol' ? 2 : 1)} {rule.unit}
                </span>
                <span className="text-xs text-gray-400 ml-1">≤{rule.threshold}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Veber Rules</h3>
        <div className="space-y-2">
          {veberRules.map((rule) => {
            const passes = rule.value <= rule.threshold;
            return (
              <div key={rule.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {passes ? (
                    <Check className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <X className="w-4 h-4 text-rose-500" />
                  )}
                  <span className="text-sm text-gray-600">{rule.name}</span>
                </div>
                <span className="text-sm text-gray-900">
                  {rule.value.toFixed(1)} {rule.unit} ≤{rule.threshold}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
