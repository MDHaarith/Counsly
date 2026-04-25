'use client';

import React, { useEffect, useCallback } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
  message: string;
  type?: ToastType;
  visible: boolean;
  onDismiss?: () => void;
}

const typeStyles: Record<ToastType, string> = {
  success: 'border-l-safe text-safe',
  error: 'border-l-error-crimson text-error-crimson',
  info: 'border-l-focus-blue text-focus-blue',
};

export function Toast({ message, type = 'info', visible, onDismiss }: ToastProps) {
  const handleDismiss = useCallback(() => {
    onDismiss?.();
  }, [onDismiss]);

  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(handleDismiss, 3000);
    return () => clearTimeout(timer);
  }, [visible, handleDismiss]);

  if (!visible) return null;

  return (
    <div
      className={[
        'fixed bottom-[72px] left-4 right-4 z-50',
        'animate-fade-in',
      ].join(' ')}
    >
      <div
        className={[
          'bg-ivory shadow-whisper rounded-card',
          'border-l-4 p-3',
          typeStyles[type],
        ].join(' ')}
      >
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-anthracite">{message}</p>
          <button
            onClick={handleDismiss}
            className="ml-3 text-stone-gray hover:text-anthracite transition-colors min-h-[44px] min-w-[44px] inline-flex items-center justify-center"
            aria-label="Dismiss"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
