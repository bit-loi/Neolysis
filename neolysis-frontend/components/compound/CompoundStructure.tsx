/* eslint-disable @next/next/no-img-element */
import { Compound } from '@/lib/types';
import { getPubChemImageUrl, getPubChemLink } from '@/lib/utils';
import { ExternalLink } from 'lucide-react';

interface CompoundStructureProps {
  compound: Compound;
}

export function CompoundStructure({ compound }: CompoundStructureProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-1">{compound.name}</h2>
      <p className="text-sm text-gray-500 mb-4">CID: {compound.cid}</p>

      <div className="flex flex-col sm:flex-row gap-6">
        <div className="flex-shrink-0">
          <img
            src={getPubChemImageUrl(compound.cid)}
            alt={`2D structure of ${compound.name}`}
            className="w-48 h-48 object-contain bg-gray-50 rounded-lg border border-gray-200"
          />
        </div>

        <div className="flex-grow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            {compound.formula ? 'Molecular Formula' : 'Molecular Identifier'}
          </h3>
          <p className="text-gray-900 mb-4">{compound.formula || `PubChem CID ${compound.cid}`}</p>

          <h3 className="text-sm font-medium text-gray-500 mb-2">SMILES</h3>
          <p className="text-sm font-mono bg-gray-50 p-2 rounded border border-gray-200 text-gray-700 break-all">
            {compound.smiles}
          </p>

          <a
            href={getPubChemLink(compound.cid)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 mt-4 px-3 py-1.5 bg-teal-100 text-teal-700 rounded-lg text-sm hover:bg-teal-200 transition-colors"
          >
            View on PubChem <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-500 mb-3">Molecular Properties</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <PropertyItem label="Molecular Weight" value={`${compound.mw.toFixed(2)} g/mol`} />
          <PropertyItem label="LogP" value={compound.logP.toFixed(2)} />
          <PropertyItem label="HBD" value={compound.hbd.toString()} />
          <PropertyItem label="HBA" value={compound.hba.toString()} />
          <PropertyItem label="TPSA" value={`${compound.tpsa.toFixed(2)} Å²`} />
          <PropertyItem label="Rotatable Bonds" value={compound.rotBonds.toString()} />
        </div>
      </div>
    </div>
  );
}

function PropertyItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-900">{value}</p>
    </div>
  );
}
