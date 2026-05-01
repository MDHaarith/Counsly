

import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  className?: string;
}

export function ProgressBar({ progress, className = '' }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, progress));

  return (
    <div
      className={[
        'h-1.5 w-full bg-warm-sand rounded-full overflow-hidden',
        className,
      ].join(' ')}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full bg-terracotta rounded-full transition-all duration-300 ease-expo"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
