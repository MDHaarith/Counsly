'use client';

import React from 'react';

interface BadgeProps {
  variant?: 'safe' | 'moderate' | 'ambitious' | 'default';
  children: React.ReactNode;
}

export function Badge({ variant = 'default', children }: BadgeProps) {
  return <span>{children}</span>;
}
