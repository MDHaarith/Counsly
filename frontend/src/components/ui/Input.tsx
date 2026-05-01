'use client';

import React, { useId } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({
  label,
  error,
  className = '',
  id: providedId,
  ...props
}: InputProps) {
  const generatedId = useId();
  const id = providedId || generatedId;

  return (
    <div className="flex flex-col">
      {label && (
        <label
          htmlFor={id}
          className="text-sm font-medium text-olive-gray mb-1.5"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={[
          'h-12 w-full rounded-xl bg-white',
          'border text-base text-anthracite placeholder:text-stone-gray',
          'px-4 outline-none transition-all duration-200',
          error
            ? 'border-error-crimson shadow-focus-ring'
            : 'border-border-cream focus:border-focus-blue focus:shadow-focus-ring',
          className,
        ].join(' ')}
        {...props}
      />
      {error && (
        <span className="text-error-crimson text-xs mt-1">{error}</span>
      )}
    </div>
  );
}
