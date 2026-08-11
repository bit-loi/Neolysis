import { RankedVariant, VariantRankResponse } from '@/lib/enzyme-api';

export function RankedVariantsTable({ result }: { result: VariantRankResponse }) {
  return (
    <section className="mt-8 border border-gray-300 bg-white p-6">
      <h2 className="font-serif text-2xl font-semibold">Ranked variants</h2>
      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="py-3 pr-4">Rank</th>
              <th className="py-3 pr-4">Variant</th>
              <th className="py-3 pr-4">Mutation summary</th>
              <th className="py-3 pr-4">Fit</th>
              <th className="py-3 pr-4">Risk</th>
              <th className="py-3 pr-4">Priority</th>
            </tr>
          </thead>
          <tbody>
            {result.ranked_variants.map((variant) => (
              <VariantRow key={variant.variant_id} variant={variant} />
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-5 text-sm text-gray-600">
        These rankings are computational estimates for candidate prioritization. Wet-lab
        validation is required before industrial use.
      </p>
    </section>
  );
}

function VariantRow({ variant }: { variant: RankedVariant }) {
  return (
    <tr className="border-b border-gray-100">
      <td className="py-4 pr-4 font-medium">#{variant.rank}</td>
      <td className="py-4 pr-4">{variant.variant_id}</td>
      <td className="max-w-md py-4 pr-4 font-mono text-xs">{variant.mutation_summary}</td>
      <td className="py-4 pr-4">{variant.predicted_fit_score.toFixed(2)}</td>
      <td className="py-4 pr-4">{variant.risk_score.toFixed(2)}</td>
      <td className="py-4 pr-4 capitalize">{variant.wet_lab_priority}</td>
    </tr>
  );
}
