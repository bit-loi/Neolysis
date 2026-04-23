import { DISEASE_LABELS, Disease } from '@/lib/types';

interface DiseaseBadgeProps {
  disease: Disease;
  size?: 'sm' | 'md';
}

export function DiseaseBadge({ disease, size = 'md' }: DiseaseBadgeProps) {
  const label = DISEASE_LABELS[disease];
  
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <span className={`inline-flex items-center rounded-none border border-gray-300 bg-white text-gray-800 font-medium font-sans uppercase tracking-widest ${sizeClasses}`}>
      {label}
    </span>
  );
}
