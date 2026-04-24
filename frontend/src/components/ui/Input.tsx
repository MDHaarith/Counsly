'use client';

import React from 'react';

interface InputProps {
  label?: string;
  type?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
}

export function Input({ label, type = 'text', value, onChange, error }: InputProps) {
  return (
    <div>
      {label && <label>{label}</label>}
      <input type={type} value={value} onChange={onChange} />
      {error && <span>{error}</span>}
    </div>
  );
}
