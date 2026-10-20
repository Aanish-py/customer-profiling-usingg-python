// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Users,
  Target,
  CalendarClock,
  AlertTriangle,
  Lightbulb,
  FileCheck2,
  Settings,
  BrainCircuit,
} from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: 'Executive Overview', path: '/', icon: LayoutDashboard },
  { name: 'Data Explorer', path: '/explorer', icon: Database },
  { name: 'Customer Profiles', path: '/customers', icon: Users },
  { name: 'Segmentation', path: '/segmentation', icon: Target },
  { name: 'Next Purchase', path: '/next-purchase', icon: CalendarClock },
  { name: 'Churn Analysis', path: '/churn', icon: AlertTriangle },
  { name: 'Recommendations', path: '/recommendations', icon: Lightbulb },
  { name: 'Model Evaluation', path: '/evaluation', icon: FileCheck2 },
  { name: 'Settings & Data', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0D1117] border-r border-border flex flex-col h-screen sticky top-0 shrink-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-border/80 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center text-white shadow-md shadow-primary/20">
          <BrainCircuit className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-text tracking-tight leading-none">Customer Intelligence</h1>
          <p className="text-[11px] text-muted mt-1 font-medium">Predictive Retail AI</p>
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-semibold text-muted tracking-wider uppercase">
          Analytics & ML Modules
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              twMerge(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150',
                isActive
                  ? 'bg-primary/10 text-primary-light border border-primary/25 shadow-sm shadow-primary/5'
                  : 'text-muted hover:text-text hover:bg-surfaceHover/70'
              )
            }
          >
            <item.icon className="w-4 h-4 shrink-0" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-border/80 bg-surface/30">
        <div className="flex items-center justify-between text-[11px] text-muted">
          <span>UCI Online Retail</span>
          <span className="flex items-center gap-1.5 text-success">
            <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
            Active
          </span>
        </div>
      </div>
    </aside>
  );
};
