'use client';

import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
}

export function ProgressBar({ progress }: ProgressBarProps) {
  return <div>{progress}%</div>;
}
