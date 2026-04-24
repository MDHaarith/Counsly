'use client';

import React from 'react';

interface UnlockOverlayProps {
  feature: string;
  children: React.ReactNode;
}

export function UnlockOverlay({ feature, children }: UnlockOverlayProps) {
  return <div>{children}</div>;
}
