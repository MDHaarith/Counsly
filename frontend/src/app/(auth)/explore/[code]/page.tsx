'use client';

import { useParams } from 'next/navigation';

export default function CollegeDetailPage() {
  const params = useParams<{ code: string }>();

  return (
    <div className="p-4">
      <h1 className="font-serif text-2xl text-anthracite">College {params.code}</h1>
    </div>
  );
}
