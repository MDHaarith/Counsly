'use client';

import { useState } from 'react';
import type { TNEAPhase } from '@/types';

export function usePhase() {
  const [phase] = useState<TNEAPhase>(1);
  const [loading] = useState(true);

  return { phase, loading };
}
