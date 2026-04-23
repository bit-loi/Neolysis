import { NextRequest, NextResponse } from 'next/server';
import { getTargetById } from '@/lib/targets';
import { getCompoundByCid } from '@/lib/docking';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { targetId, compoundCid } = body;

    if (!targetId || !compoundCid) {
      return NextResponse.json(
        { error: 'targetId and compoundCid are required' },
        { status: 400 }
      );
    }

    const target = getTargetById(targetId);
    const compound = getCompoundByCid(compoundCid);

    if (!target) {
      return NextResponse.json({ error: 'Target not found' }, { status: 404 });
    }

    if (!compound) {
      return NextResponse.json({ error: 'Compound not found' }, { status: 404 });
    }

    // Call the fastAPI backend which will execute LLM context generation
    const response = await fetch('http://127.0.0.1:8000/api/v1/narrative/insight', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_name: target.name,
        disease: target.disease,
        burden_description: target.description, // using description as burden for now
        compound_name: compound.name,
        cid: String(compound.cid),
        affinity: compound.dockingScore || 0,
        pocket: 1,
        ligand_eff: compound.ligandEfficiency || 0,
        mw: compound.mw || 0,
        logp: compound.logP || 0,
        lipinski_status: compound.lipinskiPass ? 'Pass' : 'Fail',
        confidence: compound.confidence || 0,
        explanation_from_csv: compound.explanation || ''
      })
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const { text } = await response.json();
    
    // Simulate slight loading if backend is too fast (for UI polish)
    await new Promise((resolve) => setTimeout(resolve, 300));
    
    return NextResponse.json({ text });
  } catch (error: any) {
    return NextResponse.json(
      { error: 'Internal server error: ' + error.message },
      { status: 500 }
    );
  }
}
