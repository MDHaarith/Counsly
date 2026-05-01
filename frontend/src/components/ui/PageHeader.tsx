

import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function PageHeader({ title, subtitle, className = '' }: PageHeaderProps) {
  return (
    <div className={['px-4 pt-4', className].join(' ')}>
      <h1 className="font-serif text-screen_title font-medium text-anthracite">
        {title}
      </h1>
      {subtitle && (
        <p className="text-body text-olive-gray mt-1">
          {subtitle}
        </p>
      )}
    </div>
  );
}
