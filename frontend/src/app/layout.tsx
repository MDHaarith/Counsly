import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { AppProvider } from '@/contexts/AppContext';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' });

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#faf9f5',
};

export const metadata: Metadata = {
  title: 'Counsly — Your TNEA Counselling Guide',
  description: 'Trust-first guidance for Tamil Nadu Engineering Admissions. Rank bands, college recommendations, choice filing, and more.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
      <body className="min-h-screen bg-parchment text-anthracite font-sans">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
