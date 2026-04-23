'use client';

import { motion } from 'framer-motion';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  centered?: boolean;
}

export function SectionHeader({ title, subtitle, centered = true }: SectionHeaderProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`mb-12 ${centered ? 'text-center flex flex-col items-center' : ''}`}
    >
      <h2 className="text-4xl md:text-5xl font-serif font-bold text-black mb-4 tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-lg text-gray-700 max-w-2xl mx-auto font-sans leading-relaxed">
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-rose-100 text-rose-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium font-sans ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
