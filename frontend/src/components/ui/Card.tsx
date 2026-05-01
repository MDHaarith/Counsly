

import React from 'react';

type CardVariant = 'standard' | 'featured';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  children: React.ReactNode;
}

const variantStyles: Record<CardVariant, string> = {
  standard: [
    'bg-ivory border border-border-cream rounded-card p-4',
    'hover:shadow-whisper transition-shadow',
  ].join(' '),
  featured: [
    'bg-ivory shadow-whisper rounded-card-lg p-5',
  ].join(' '),
};

export function Card({
  variant = 'standard',
  className = '',
  children,
  onClick,
  ...props
}: CardProps) {
  const handleClick = onClick
    ? (e: React.MouseEvent<HTMLDivElement>) => {
        onClick(e);
      }
    : undefined;

  const handleKeyDown = onClick
    ? (e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e as unknown as React.MouseEvent<HTMLDivElement>);
        }
      }
    : undefined;

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={[variantStyles[variant], className].join(' ')}
      {...props}
    >
      {children}
    </div>
  );
}
