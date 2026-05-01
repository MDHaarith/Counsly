

import React from 'react';

type BadgeVariant = 'safe' | 'moderate' | 'ambitious' | 'default';

interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  safe: 'bg-safe/10 text-safe',
  moderate: 'bg-moderate/10 text-moderate',
  ambitious: 'bg-ambitious/10 text-ambitious',
  default: 'bg-surface-alt text-stone-gray',
};

export function Badge({
  variant = 'default',
  className = '',
  children,
}: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center',
        'text-badge font-medium leading-tight',
        'px-2 py-0.5 rounded-md',
        variantStyles[variant],
        className,
      ].join(' ')}
    >
      {children}
    </span>
  );
}
