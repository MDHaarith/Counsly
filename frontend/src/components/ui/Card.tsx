'use client';

import React from 'react';

interface CardProps {
  variant?: 'standard' | 'featured';
  className?: string;
  children: React.ReactNode;
}

export function Card({ variant = 'standard', className, children }: CardProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}
