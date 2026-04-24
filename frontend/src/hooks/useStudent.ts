'use client';

import { useState } from 'react';
import type { StudentProfile } from '@/types';

export function useStudent() {
  const [student] = useState<StudentProfile | null>(null);
  const [isLoading] = useState(true);

  return { student, isLoading };
}
