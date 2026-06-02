'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/analyze', label: 'Analyze' },
  { href: '/variants', label: 'Variants' },
  { href: '/agent-report', label: 'Agent Report' },
  { href: '/methodology', label: 'Methodology' },
  { href: '/about', label: 'About' },
];

const experimentalNavLinks =
  process.env.NEXT_PUBLIC_ENABLE_MD_ENGINE === 'true'
    ? [{ href: '/experimental/md-sandbox', label: 'MD Sandbox' }]
    : [];

const visibleNavLinks = [...navLinks, ...experimentalNavLinks];

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const isHomepage = pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const showDark = isHomepage && !scrolled;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        showDark
          ? 'bg-transparent'
          : 'bg-white/95 backdrop-blur-md border-b border-gray-100 shadow-sm'
      }`}
    >
      <nav className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex h-20 items-center justify-between">

          {/* Logo */}
          <Link href="/" className="flex items-center">
            <Image
              src={showDark ? '/logo-white.png' : '/logo.png'}
              alt="Neolysis"
              width={144}
              height={80}
              priority
              className="h-14 w-auto object-contain transition duration-500"
            />
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex md:items-center md:gap-10">
            {visibleNavLinks.map((link) => {
              const isActive = pathname === link.href;

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative text-sm font-medium tracking-wide transition-colors duration-300
                  
                  after:absolute after:left-0 after:-bottom-1 after:h-[2px] 
                  after:w-0 after:bg-current after:transition-all after:duration-300
                  
                  ${
                    isActive
                      ? 'after:w-full'
                      : 'hover:after:w-full'
                  }

                  ${
                    isActive
                      ? showDark
                        ? 'text-[#B2D8E5]'
                        : 'text-[#5BA8B9]'
                      : showDark
                      ? 'text-white/70 hover:text-white'
                      : 'text-gray-500 hover:text-gray-900'
                  }
                  
                  `}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile Button */}
          <button
            type="button"
            className={`md:hidden p-2 transition-colors ${
              showDark ? 'text-white' : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100">
          <div className="px-6 py-4 space-y-1">
            {visibleNavLinks.map((link) => {
              const isActive = pathname === link.href;

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`block px-4 py-3 text-base font-medium transition-colors
                  ${
                    isActive
                      ? 'text-[#5BA8B9]'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
