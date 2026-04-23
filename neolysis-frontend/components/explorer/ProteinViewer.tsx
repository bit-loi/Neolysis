'use client';

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
  const [hasRCSB, setHasRCSB] = useState(true);
  const [lib3DmolReady, setLib3DmolReady] = useState(false);
  const scriptLoaded = useRef(false);
  const initStarted = useRef(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Already loaded from a previous mount
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

    // Always clear existing surfaces first
    viewer.removeAllSurfaces();

    if (style === 'surface') {
      // Show a faint cartoon underneath so the surface has context
      viewer.setStyle({}, { cartoon: { color: 'spectrum', opacity: 0.4 } });
      viewer.addSurface(
        window.$3Dmol.SurfaceType.VDW,
        { opacity: 0.8, color: 'white' },
        {},
      );
    } else if (style === 'stick') {
      viewer.setStyle({}, { stick: { colorscheme: 'Jmol' } });
    } else {
      viewer.setStyle({}, { cartoon: { color: 'spectrum', opacity: 0.85 } });
    }

    viewer.render();
  };

  useEffect(() => {
    if (viewer) updateStyle();
  }, [style, viewer]);

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
        <div className="flex flex-wrap gap-4">
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
        </div>
      </div>
    </motion.div>
  );
}
