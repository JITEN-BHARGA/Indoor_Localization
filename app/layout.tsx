export const metadata = {
  title: 'Indoor Localization Dashboard',
  description: 'Wi-Fi RSSI fingerprinting project dashboard'
};

import './globals.css';
import type { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
