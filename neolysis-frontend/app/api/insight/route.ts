import { NextResponse } from 'next/server';

export async function POST() {
  return NextResponse.json(
    {
      error: 'The legacy drug-discovery insight endpoint is deprecated.',
      replacement: '/api/v1/agents/analyze',
    },
    { status: 410 },
  );
}
