

import React from 'react';

interface UnlockOverlayProps {
  feature: string;
  children: React.ReactNode;
  onUnlock: () => void;
}

export function UnlockOverlay({ feature, children, onUnlock }: UnlockOverlayProps) {
  return (
    <div className="relative">
      {children}
      <div
        className={[
          'absolute inset-0 z-10',
          'bg-parchment/80 backdrop-blur-[2px]',
          'rounded-card flex flex-col items-center justify-center',
          'animate-fade-in',
        ].join(' ')}
      >
        {/* Lock icon */}
        <div className="mb-3 text-stone-gray">
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>

        <p className="font-serif text-card_title font-medium text-anthracite mb-1">
          Full Access
        </p>

        <p className="text-body text-olive-gray text-center px-6 mb-5 max-w-[200px]">
          {feature}
        </p>

        <button
          onClick={onUnlock}
          className={[
            'h-12 px-6 rounded-xl',
            'bg-terracotta text-ivory',
            'font-medium text-sm',
            'active:scale-[0.98] transition-transform duration-200',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-terracotta/30',
          ].join(' ')}
        >
          Unlock
        </button>
      </div>
    </div>
  );
}
