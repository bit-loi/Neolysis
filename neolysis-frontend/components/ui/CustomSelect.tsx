'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface Option {
  label: string;
  value: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (val: string) => void;
  options: Option[];
}

export function CustomSelect({ value, onChange, options }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((o) => o.value === value) || options[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative font-sans" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-40 px-3 py-1.5 text-sm font-bold bg-white text-black border border-gray-400 hover:border-black transition-colors focus:outline-none"
      >
        <span>{selectedOption.label}</span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 shadow-md">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className={`w-full text-left px-3 py-2 text-sm font-bold transition-colors ${
                value === option.value
                  ? 'bg-black text-white'
                  : 'bg-white text-gray-800 hover:bg-gray-100 hover:text-black'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
