'use client';
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Box } from 'lucide-react';
import { getPdbUrl } from '@/lib/utils';
import { motion } from 'framer-motion';
import { LottieAnimation } from '@/components/ui/LottieAnimation';
import sandyLoadingData from '@/public/Sandy Loading.json';
import emptyStateData from '@/public/no result found.json';

interface ProteinViewerProps {
  pdbId: string;
  proteinName: string;
  alphafoldId?: string;
}

declare global {
  interface Window {
    $3Dmol: any;
  }
}

export function ProteinViewer({ pdbId, proteinName, alphafoldId }: ProteinViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewer, setViewer] = useState<any>(null);
  const [style, setStyle] = useState<'cartoon' | 'stick' | 'surface'>('cartoon');
  const [showDemoCombo, setShowDemoCombo] = useState(false);
  const [hasRCSB, setHasRCSB] = useState(true);
  const [lib3DmolReady, setLib3DmolReady] = useState(false);
  const [insightData, setInsightData] = useState<any>(null);
  const [isLoadingInsight, setIsLoadingInsight] = useState(false);
  const [insightError, setInsightError] = useState<string | null>(null);
  
  const scriptLoaded = useRef(false);
  const initStarted = useRef(false);

  useEffect(() => {
    if (showDemoCombo && !insightData && !isLoadingInsight && !insightError) {
      const fetchInsight = async () => {
        setIsLoadingInsight(true);
        setInsightError(null);
        try {
          const res = await fetch('http://localhost:8000/api/v1/insight/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              protein_name: proteinName,
              query: "Provide a concise structural analysis of the 3D binding site and key interacting residues for targeted inhibition. Write in English."
            })
          });
          if (!res.ok) {
            throw new Error('Failed to fetch AI insight');
          }
          const data = await res.json();
          setInsightData(data);
        } catch (err: any) {
          setInsightError(err.message || 'An error occurred while fetching insight.');
        } finally {
          setIsLoadingInsight(false);
        }
      };
      fetchInsight();
    }
  }, [showDemoCombo, proteinName, insightData, isLoadingInsight, insightError]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    if (window.$3Dmol) {
      setLib3DmolReady(true);
      return;
    }

    if (scriptLoaded.current) return;
    scriptLoaded.current = true;

    const script = document.createElement('script');
    script.src = 'https://3dmol.org/build/3Dmol-min.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.onload = () => {
      setLib3DmolReady(true);
    };
    script.onerror = () => {
      setError('Failed to load 3D viewer library');
      setIsLoading(false);
    };
    document.body.appendChild(script);
  }, []);

  const loadStructure = useCallback(async (v: any) => {
    let url = getPdbUrl(pdbId);
    let response = await fetch(url);
    
    if (!response.ok && alphafoldId) {
      setHasRCSB(false);
      url = `https://alphafold.ebi.ac.uk/files/${alphafoldId}-F1-model_v4.pdb`;
      response = await fetch(url);
    }
    
    if (!response.ok) {
      setError('Structure not available');
      return false;
    }
    
    const pdbData = await response.text();
    try {
      v.addModel(pdbData, 'pdb');
      v.setStyle({}, { cartoon: { color: 'spectrum', opacity: 0.85 } });
      v.zoomTo();
      v.render();
      v.zoom(0.8, 500);
      setViewer(v);
    } catch (e) {
      setError('Failed to render structure');
    }
    return true;
  }, [pdbId, alphafoldId]);

  useEffect(() => {
    if (!viewerRef.current || initStarted.current || !lib3DmolReady) return;
    initStarted.current = true;

    const initViewer = async () => {
      setIsLoading(true);
      setError(null);
      
      const v = window.$3Dmol.createViewer(viewerRef.current, {
        backgroundColor: '#ffffff',
      });
      
      try {
        await loadStructure(v);
      } catch (err) {
        setError('Failed to load protein structure');
      } finally {
        setIsLoading(false);
      }
    };

    initViewer();
  }, [pdbId, alphafoldId, lib3DmolReady, loadStructure]);

  const updateStyle = () => {
    if (!viewer) return;

    // Clear existing surfaces, shapes, and labels
    viewer.removeAllSurfaces();
    viewer.removeAllShapes();
    viewer.removeAllLabels();

    // Base Style
    if (style === 'surface') {
      viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
      viewer.addSurface(
        window.$3Dmol.SurfaceType.VDW,
        { opacity: 0.8, color: 'white' },
        {},
      );
    } else if (style === 'stick') {
      viewer.setStyle({}, { stick: { colorscheme: 'Jmol' } });
    } else {
      viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
    }

    // AI DEMO COMBO (Highlighting binding site & interactions)
    if (showDemoCombo) {
      try {
        const model = viewer.getModel(0);
        const atoms = model.selectedAtoms({});
        if (atoms && atoms.length > 0) {
          const extent = window.$3Dmol.getExtent(atoms);
          
          // Calculate center of the protein
          const cx = (extent[0][0] + extent[1][0]) / 2;
          const cy = (extent[0][1] + extent[1][1]) / 2;
          const cz = (extent[0][2] + extent[1][2]) / 2;

          // Find the maximum distance from center
          let maxDist = 0;
          atoms.forEach((a: any) => {
            const d = Math.sqrt(Math.pow(a.x - cx, 2) + Math.pow(a.y - cy, 2) + Math.pow(a.z - cz, 2));
            if (d > maxDist) maxDist = d;
          });
          
          // Target a deeply buried pocket (e.g. 35% from center to edge, representing a deep cleft)
          const targetDist = maxDist * 0.35;
          let bestAtom = atoms[0];
          let bestDiff = 9999;
          
          // Catalytic residues common in active sites
          const catalyticRes = ['HIS', 'SER', 'CYS', 'GLU', 'ASP'];
          
          // 1st pass: Find deeply buried catalytic CA
          atoms.forEach((a: any) => {
            const d = Math.sqrt(Math.pow(a.x - cx, 2) + Math.pow(a.y - cy, 2) + Math.pow(a.z - cz, 2));
            const diff = Math.abs(d - targetDist);
            if (diff < bestDiff && a.atom === 'CA' && catalyticRes.includes(a.resn)) {
              bestDiff = diff;
              bestAtom = a;
            }
          });
          
          // 2nd pass: Fallback if no catalytic residue found
          if (bestDiff === 9999) {
            atoms.forEach((a: any) => {
              const d = Math.sqrt(Math.pow(a.x - cx, 2) + Math.pow(a.y - cy, 2) + Math.pow(a.z - cz, 2));
              const diff = Math.abs(d - targetDist);
              if (diff < bestDiff && a.atom === 'CA') {
                bestDiff = diff;
                bestAtom = a;
              }
            });
          }
          
          const baseResi = bestAtom.resi;

          // 1. Highlight specific residues (Interacting residues) using a robust 3D spatial search
          const nearbyResi = new Set<number>();
          atoms.forEach((a: any) => {
            if (a.atom === 'CA') {
              const dist = Math.sqrt(
                Math.pow(a.x - bestAtom.x, 2) + 
                Math.pow(a.y - bestAtom.y, 2) + 
                Math.pow(a.z - bestAtom.z, 2)
              );
              // Find surrounding residues within an 8 Angstrom radius
              if (dist > 0 && dist < 8.0) {
                nearbyResi.add(a.resi);
              }
            }
          });
          
          // Include the anchor and up to 6 spatial neighbors
          const interactingResi = [bestAtom.resi, ...Array.from(nearbyResi).slice(0, 6)];
          viewer.addStyle({resi: interactingResi}, { stick: { color: "yellow", radius: 0.15 } });

          // Calculate the true geometric center of these specific residues to perfectly center the box
          let sumX = 0, sumY = 0, sumZ = 0, count = 0;

          // Identify key residues with labels and calculate true center
          interactingResi.forEach(r => {
            const resAtoms = atoms.filter((a: any) => a.resi === r && a.atom === 'CA');
            if (resAtoms.length > 0) {
              const target = resAtoms[0];
              
              sumX += target.x;
              sumY += target.y;
              sumZ += target.z;
              count++;
              
              // Capitalize first letter of residue name (e.g. "His", "Asp")
              const resName = target.resn ? target.resn.charAt(0) + target.resn.slice(1).toLowerCase() : 'Res';
              viewer.addLabel(`${resName}${r}`, {
                position: { x: target.x, y: target.y, z: target.z },
                fontColor: "#fbbf24", // yellow-400
                fontSize: 12,
                showBackground: false
              });
            }
          });
          
          const pocketCenter = count > 0 
            ? { x: sumX / count, y: sumY / count, z: sumZ / count }
            : { x: bestAtom.x, y: bestAtom.y, z: bestAtom.z };

          // 2. Add AutoDock Vina Grid Box (Visualizing the docking search space)
          viewer.addBox({
            center: pocketCenter,
            dimensions: { w: 26, h: 26, d: 26 }, // Increased size to 26A to cover all residues
            color: "green",
            alpha: 0.5,
            wireframe: true
          });

          // 3. Add Marker Sphere for Binding Pocket Centroid (Smaller)
          viewer.addSphere({
            center: pocketCenter,
            radius: 1.2,
            color: "red",
            alpha: 0.9
          });

          // 4. Add General AI Label slightly above the box
          viewer.addLabel("Optimal Binding Pocket", {
            position: { x: pocketCenter.x, y: pocketCenter.y + 14, z: pocketCenter.z },
            backgroundColor: "white",
            fontColor: "black",
            backgroundOpacity: 0.9,
            borderColor: "black",
            borderThickness: 1.0
          });

          // Focus on the binding site safely
          // Restrict zoom selection to the specific chain of our anchor atom 
          // to prevent multi-chain residue collisions from exploding the bounding box.
          const zoomSelection: any = { resi: interactingResi };
          if (bestAtom.chain) {
            zoomSelection.chain = bestAtom.chain;
          }
          viewer.zoomTo(zoomSelection);
          viewer.zoom(0.8, 1000); // zoom out slightly so the 26A grid box fits beautifully
        }
      } catch (e) {
        console.error("Error rendering demo combo:", e);
      }
    }

    viewer.render();
  };

  useEffect(() => {
    if (viewer) updateStyle();
  }, [style, showDemoCombo, viewer]);

  const handleReset = () => {
    if (!viewer) return;
    viewer.zoomTo();
    viewer.zoom(0.8, 500);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1, ease: 'easeOut' }}
      className="bg-white border border-gray-300 overflow-hidden font-sans flex flex-col h-full"
    >
      <div className="p-4 border-b border-gray-300 bg-[#f5f5f0]">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-serif font-bold text-xl text-black">{proteinName}</h3>
            <p className="text-sm text-gray-600 font-mono">PDB: {pdbId}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              disabled={isLoading || !!error}
              className={`p-2 text-gray-800 transition-colors ${
                isLoading || error ? 'opacity-50 cursor-not-allowed' : 'hover:text-black hover:bg-white border border-transparent hover:border-gray-300'
              }`}
              title="Reset view"
            >
              <Box className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="relative h-80 sm:h-96 flex flex-col items-center justify-center bg-[#f5f5f0] flex-grow">
        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#f5f5f0] z-20">
            <LottieAnimation animationData={sandyLoadingData} size="md" />
            <p className="mt-2 text-sm font-bold text-gray-600">Loading protein structure...</p>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#f5f5f0] z-20 text-center p-4">
            <LottieAnimation animationData={emptyStateData} size="md" loop={false} />
            <p className="mt-4 text-sm font-bold text-gray-600">Structure data not yet available.</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 text-sm font-bold bg-white text-black border border-gray-400 hover:border-black transition-colors"
            >
              Reload
            </button>
          </div>
        )}

        <div ref={viewerRef} className="w-full h-full relative z-0" />
      </div>

      <div className="p-4 border-t border-gray-300 bg-white">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className={`flex items-center gap-3 ${isLoading || error ? 'opacity-50 pointer-events-none' : ''}`}>
            <span className="text-xs font-bold text-black uppercase tracking-wider">Style:</span>
            <div className="flex gap-2">
              {(['cartoon', 'stick', 'surface'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setStyle(s)}
                  className={`px-3 py-1 text-sm font-bold transition-colors border ${
                    style === s
                      ? 'bg-black text-white border-black'
                      : 'bg-white text-gray-800 border-gray-400 hover:border-black hover:text-black'
                  }`}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          {/* AI DEMO TOGGLE */}
          <button
            onClick={() => setShowDemoCombo(!showDemoCombo)}
            disabled={isLoading || !!error}
            className={`flex items-center gap-2 px-4 py-1.5 text-sm font-bold border transition-all ${
              showDemoCombo 
                ? 'bg-green-100 text-green-800 border-green-500 shadow-inner' 
                : 'bg-white text-gray-800 border-gray-400 hover:border-black hover:text-black'
            } ${isLoading || error ? 'opacity-50 pointer-events-none' : ''}`}
          >
            {showDemoCombo ? 'Hide Target Site Analysis' : 'Analyze Target Site'}
          </button>
        </div>
      </div>

      {/* GEMMA 4 INSIGHT PANEL */}
      {showDemoCombo && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-white p-5 sm:p-6 border-t-4 border-green-600 shadow-inner"
        >
          <div className="flex items-start gap-4">
            <div className="w-full">
              <h4 className="font-sans font-bold text-green-800 mb-2 flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full border border-green-200 ${isLoadingInsight ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></span>
                Gemma 4 Insight: Structural Binding Analysis
              </h4>
              
              {isLoadingInsight ? (
                <div className="flex items-center gap-2 text-sm text-gray-500 mt-4">
                  <LottieAnimation animationData={sandyLoadingData} size="sm" />
                  Gemma 4 is analyzing structural data...
                </div>
              ) : insightError ? (
                <p className="text-red-600 text-sm mt-2">{insightError}</p>
              ) : insightData ? (
                <div className="mt-3">
                  <p className="text-gray-700 text-sm leading-relaxed mb-3">
                    {insightData.summary}
                  </p>
                  {insightData.drug_assessment && (
                    <p className="text-gray-700 text-sm leading-relaxed">
                      <strong>Binding Assessment:</strong> {insightData.drug_assessment}
                    </p>
                  )}
                  {insightData.fallback && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded-md">
                      <strong>Note:</strong> This analysis was generated without grounded literature context. Please run the PubMed crawler to enrich the Knowledge Graph for this target.
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
