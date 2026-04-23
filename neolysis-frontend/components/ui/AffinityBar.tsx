'use client';

interface AffinityBarProps {
  affinity: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function AffinityBar({ affinity, showLabel = true, size = 'md' }: AffinityBarProps) {
  const getColor = (affinity: number) => {
    if (affinity < -8) return 'bg-green-500';
    if (affinity <= -5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getLabel = (affinity: number) => {
    if (affinity < -8) return 'Strong';
    if (affinity <= -5) return 'Moderate';
    return 'Weak';
  };

  const normalizedScore = Math.min(Math.max((affinity + 12) / 14 * 100, 0), 100);
  
  const heights = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="flex flex-col gap-1">
      <div className={`w-full ${heights[size]} bg-gray-200 rounded-full overflow-hidden`}>
        <div
          className={`${heights[size]} ${getColor(affinity)} rounded-full transition-all duration-500`}
          style={{ width: `${normalizedScore}%` }}
        />
      </div>
      {showLabel && (
        <div className={`${textSizes[size]} font-bold text-gray-700`}>
          {affinity.toFixed(2)} kcal/mol — {getLabel(affinity)}
        </div>
      )}
    </div>
  );
}