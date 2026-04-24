'use client';

import React from 'react';

interface SheetProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export function Sheet({ open, onClose, title, children }: SheetProps) {
  if (!open) return null;
  return (
    <div>
      {title && <h2>{title}</h2>}
      {children}
    </div>
  );
}
