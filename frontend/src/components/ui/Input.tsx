'use client';

import React, { useId } from 'react';

interface InputProps {
  label?: string;
  type?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  placeholder?: string;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
  className?: string;
}

export function Input({
  label,
  type = 'text',
  value,
  defaultValue,
  onChange,
  onBlur,
  error,
  placeholder,
  inputMode,
  className = '',
}: InputProps) {
  const id = useId();

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
        type={type}
        value={value}
        defaultValue={defaultValue}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        inputMode={inputMode}
        className={[
          'h-12 w-full rounded-xl bg-white',
          'border text-base text-anthracite placeholder:text-stone-gray',
          'px-4 outline-none transition-all duration-200',
          error
            ? 'border-error-crimson shadow-focus-ring'
            : 'border-border-cream focus:border-focus-blue focus:shadow-focus-ring',
          className,
        ].join(' ')}
      />
      {error && (
        <span className="text-error-crimson text-xs mt-1">{error}</span>
      )}
    </div>
  );
}
