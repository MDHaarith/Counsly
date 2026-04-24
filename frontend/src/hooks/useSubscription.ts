'use client';

import { useState } from 'react';
import type { AccessTier } from '@/types';

export function useSubscription() {
  const [tier] = useState<AccessTier>('free');
  const [isLoading] = useState(true);

  return { tier, isLoading };
}
