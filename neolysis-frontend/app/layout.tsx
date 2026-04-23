import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { ToastProvider } from '@/components/ui/Toast';

export const metadata: Metadata = {
  title: 'Neolysis — AI Drug Discovery for ASEAN NTD Research',
  description: 'Open-access platform for leptospirosis, scrub typhus, melioidosis, and dengue research. Explore 3D protein structures, pre-computed docking scores, and AI-generated insights.',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-white font-sans antialiased">
        <ToastProvider>
          <Navbar />
          <main className="flex-grow">{children}</main>
          <Footer />
        </ToastProvider>
      </body>
    </html>
  );
}
