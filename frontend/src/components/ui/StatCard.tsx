// frontend/src/components/ui/StatCard.tsx
import React from 'react';
import { LucideIcon } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: LucideIcon;
  iconColor?: string;
  className?: string;
  caption?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  iconColor = 'text-primary-light',
  className,
  caption,
}) => {
  return (
    <div
      className={twMerge(
        'bg-surface border border-border rounded-xl p-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted tracking-wider uppercase">{label}</span>
        {Icon && (
          <div className={twMerge('p-2 rounded-lg bg-surfaceHover border border-border/60', iconColor)}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-text">{value}</span>
        {change && (
          <span
            className={twMerge(
              'text-xs font-medium px-1.5 py-0.5 rounded',
              changeType === 'positive' && 'text-success bg-success/10 border border-success/20',
              changeType === 'negative' && 'text-danger bg-danger/10 border border-danger/20',
              changeType === 'neutral' && 'text-muted bg-surfaceHover border border-border'
            )}
          >
            {change}
          </span>
        )}
      </div>

      {caption && <p className="mt-1 text-xs text-muted">{caption}</p>}
    </div>
  );
};
