import { QuantumTab } from '@/lib/quantum';

const tabs: Array<{ id: QuantumTab; label: string }> = [
  { id: 'comparison', label: 'Solver Comparison Cards & Selection Table' },
  { id: 'qubo', label: 'QUBO Formulation & Penalty Terms' },
  { id: 'disclaimer', label: 'Methodology & Limitations' },
];

interface QuantumTabsProps {
  activeTab: QuantumTab;
  onSelectTab: (tab: QuantumTab) => void;
}

export function QuantumTabs({ activeTab, onSelectTab }: QuantumTabsProps) {
  return (
    <div className="flex flex-wrap gap-6 border-b border-slate-800">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onSelectTab(tab.id)}
          className={`border-b-2 pb-3 text-sm font-medium transition ${
            activeTab === tab.id
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
