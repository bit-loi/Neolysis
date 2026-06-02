'use client';

import { motion, useInView } from 'framer-motion';
import { useRef, useState, useMemo } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';

// Deterministic seeded PRNG to avoid hydration mismatch
function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return s / 2147483647;
  };
}

function generateBinaryPattern() {
  const rng = seededRandom(42);
  return Array.from({ length: 80 }, () =>
    Array.from({ length: 120 }, () => Math.round(rng())).join(' ')
  ).join('\n');
}

const articles = [
  {
    tag: 'Research Update',
    title: 'Neolysis Maps 12 Key Protein Targets Across 4 ASEAN NTDs',
    description:
      'Our latest computational pipeline has identified and validated 12+ drug targets spanning leptospirosis, scrub typhus, melioidosis, and dengue.',
  },
  {
    tag: 'Platform Release',
    title: 'Interactive 3D Protein Visualization Now Live',
    description:
      'Researchers can now explore AlphaFold-predicted protein structures through an interactive 3D viewer — no software installation required.',
  },
  {
    tag: 'AI Insights',
    title: 'Gemini-Powered Drug Candidate Analysis for Dengue Targets',
    description:
      'Our AI insight engine now generates contextual narratives explaining why certain compound-target pairs show therapeutic promise.',
  },
  {
    tag: 'Open Data',
    title: 'Pre-computed Docking Scores Available for All Targets',
    description:
      'AutoDock Vina docking results for every protein target are now freely accessible, enabling rapid comparison of drug candidates.',
  },
  {
    tag: 'Community',
    title: 'Neolysis Hackathon: Building Tools for NTD Research',
    description:
      'Join developers and researchers worldwide in building open-source computational tools for neglected tropical disease discovery.',
  },
  {
    tag: 'Methodology',
    title: 'How We Validate Protein Targets Using AlphaFold DB',
    description:
      'A deep dive into our target validation pipeline combining structural biology databases with confidence scoring for ASEAN-relevant pathogens.',
  },
];

const featuredArticle = {
  tag: 'Neolysis · AI Drug Discovery · NTD Research',
  title: 'Accelerating Drug Discovery for ASEAN\'s Most Neglected Diseases',
};

export function NewsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrollIndex, setScrollIndex] = useState(0);
  const binaryPattern = useMemo(() => generateBinaryPattern(), []);
  void binaryPattern;

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return;
    const cardWidth = 360;
    const maxIndex = Math.max(0, articles.length - 2);
    const newIndex = direction === 'left'
      ? Math.max(0, scrollIndex - 1)
      : Math.min(maxIndex, scrollIndex + 1);

    setScrollIndex(newIndex);
    scrollRef.current.scrollTo({
      left: newIndex * cardWidth,
      behavior: 'smooth',
    });
  };

  return (
    <section ref={ref} className="relative overflow-hidden">
      {/* Featured Header - Dark section */}
      <div className="bg-[#081e24] relative grain-overlay py-24 lg:py-32">

        <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8">
          <motion.p
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ duration: 0.5 }}
            className="text-sm text-gray-400 uppercase tracking-wider mb-6"
          >
            {featuredArticle.tag}
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-serif text-white max-w-3xl leading-tight"
          >
            {featuredArticle.title}
          </motion.h2>
        </div>
      </div>

      {/* Articles Carousel - Light section */}
      <div className="py-16 section-light">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          {/* Section title + Navigation */}
          <div className="flex items-center justify-between mb-10">
            <motion.h3
              initial={{ opacity: 0 }}
              animate={isInView ? { opacity: 1 } : {}}
              transition={{ delay: 0.4 }}
              className="text-sm text-gray-500 uppercase tracking-wider"
            >
              What&apos;s Happening
            </motion.h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => scroll('left')}
                className="w-12 h-12 rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:border-gray-900 hover:text-gray-900 transition-colors disabled:opacity-30"
                disabled={scrollIndex === 0}
                aria-label="Previous articles"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => scroll('right')}
                className="w-12 h-12 rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:border-gray-900 hover:text-gray-900 transition-colors disabled:opacity-30"
                disabled={scrollIndex >= articles.length - 2}
                aria-label="Next articles"
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Scrollable Cards */}
          <div
            ref={scrollRef}
            className="flex gap-6 overflow-x-auto hide-scrollbar pb-4"
          >
            {articles.map((article, i) => (
              <motion.article
                key={article.title}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.5 + i * 0.08, duration: 0.5 }}
                className="flex-shrink-0 w-[340px] group cursor-pointer"
              >
                {/* Card image area */}
                <div className="w-full h-48 bg-navy-light rounded-lg mb-4 relative overflow-hidden grain-overlay">
                  <div className="absolute inset-0 bg-gradient-to-br from-[#1a3a5c] to-[#0f1120] opacity-90" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[#B2D8E5] font-serif text-3xl italic opacity-30 select-none">
                      N
                    </span>
                  </div>
                </div>
                <span className="text-xs text-gray-500 uppercase tracking-wider">
                  {article.tag}
                </span>
                <h4 className="mt-2 text-lg font-serif text-gray-900 group-hover:text-[#5BA8B9] transition-colors leading-snug">
                  {article.title}
                </h4>
              </motion.article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
