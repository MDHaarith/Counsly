'use client';

import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    'w-full bg-terracotta text-ivory',
    'hover:bg-terracotta/90',
    'active:bg-terracotta/80 active:scale-[0.98]',
  ].join(' '),
  secondary: [
    'bg-warm-sand text-anthracite',
    'hover:bg-warm-sand/80',
    'active:bg-warm-sand/70 active:scale-[0.98]',
  ].join(' '),
  ghost: [
    'bg-transparent text-terracotta',
    'hover:bg-terracotta/5',
    'active:bg-terracotta/10 active:scale-[0.98]',
  ].join(' '),
};

export function Button({
  variant = 'primary',
  className = '',
  children,
  disabled,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={[
        'inline-flex items-center justify-center',
        'h-12 px-4 rounded-xl',
        'font-medium text-sm leading-none',
        'transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-terracotta/30',
        'disabled:opacity-50 disabled:pointer-events-none',
        variantStyles[variant],
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </button>
  );
}
