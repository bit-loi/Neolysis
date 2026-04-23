'use client';

import Link from 'next/link';
import Image from 'next/image';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ArrowRight } from 'lucide-react';

export function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <>
      {/* Community & Learning — Split layout */}
      <section ref={ref} className="bg-white">
        <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[600px]">
          {/* Left: Illustration */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ duration: 0.8 }}
            className="relative bg-[#d4e8d4] overflow-hidden"
          >
            <div className="absolute inset-0 grain-overlay" />
            <Image
              src="/community-illustration.jpg"
              alt="Neolysis research community"
              fill
              className="object-cover mix-blend-multiply opacity-80"
            />
          </motion.div>

          {/* Right: Content */}
          <div className="flex items-center px-8 sm:px-12 lg:px-16 py-16 lg:py-24">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <h2 className="text-4xl sm:text-5xl font-serif text-gray-900 leading-tight">
                Open Science{' '}
                <br />
                <em className="italic text-gray-500">for Everyone</em>
              </h2>
              <p className="mt-6 text-gray-600 text-lg leading-relaxed max-w-lg">
                Our community encourages collaboration between researchers,
                students, and developers worldwide. Every insight shared
                accelerates drug discovery for diseases that affect millions
                across ASEAN.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/about"
                  className="btn-bordered btn-bordered-dark"
                >
                  <ArrowRight className="h-4 w-4" />
                  Learn About Neolysis
                </Link>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Bottom CTA Bar */}
      <section className="bg-[#081e24] grain-overlay relative py-20 lg:py-24 overflow-hidden">
        <div className="relative z-10 mx-auto max-w-4xl px-6 lg:px-8 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl sm:text-4xl font-serif text-[#B2D8E5] mb-4"
          >
            Ready to discover? Start exploring today
          </motion.h2>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-8"
          >
            <Link
              href="/targets"
              className="btn-bordered btn-bordered-light text-lg"
            >
              <ArrowRight className="h-5 w-5" />
              Get started with Neolysis
            </Link>
          </motion.div>
        </div>
      </section>
    </>
  );
}
