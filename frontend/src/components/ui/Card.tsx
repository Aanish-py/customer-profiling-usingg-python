// frontend/src/components/ui/Card.tsx
import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  action,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        'bg-surface border border-border rounded-xl p-5 shadow-sm transition-all duration-200',
        className
      )}
      {...props}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 border-b border-border/50 pb-3">
          <div>
            {title && <h3 className="text-base font-semibold text-text tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
