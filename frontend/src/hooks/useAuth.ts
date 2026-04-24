'use client';

import { useState } from 'react';

interface User {
  id: string;
  email: string;
}

export function useAuth() {
  const [user] = useState<User | null>(null);
  const [isAuthenticated] = useState(false);
  const [loading] = useState(true);

  return { user, isAuthenticated, loading };
}
