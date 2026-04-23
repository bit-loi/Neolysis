const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchDockingByTarget(targetId: string) {
  const res = await fetch(`${API_BASE}/docking-csv/target/${targetId}`, {
    cache: 'force-cache',
    next: { revalidate: 3600 },
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch docking data');
  }
  
  return res.json();
}

export async function fetchDockingByCompound(cid: number) {
  const res = await fetch(`${API_BASE}/docking-csv/compound/${cid}`, {
    cache: 'force-cache',
    next: { revalidate: 3600 },
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch docking data');
  }
  
  return res.json();
}

export async function fetchAllTargets() {
  const res = await fetch(`${API_BASE}/docking-csv/targets`, {
    cache: 'force-cache',
    next: { revalidate: 3600 },
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch targets');
  }
  
  return res.json();
}

export function getAffinityColor(affinity: number): string {
  if (affinity < -8) return 'bg-green-500';
  if (affinity <= -5) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function getAffinityLabel(affinity: number): string {
  if (affinity < -8) return 'Strong';
  if (affinity <= -5) return 'Moderate';
  return 'Weak';
}

export function formatAffinity(affinity: number): string {
  return `${affinity.toFixed(2)} kcal/mol`;
}