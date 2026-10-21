'use client';

import React from 'react';
import { Activity } from 'lucide-react';
import { ActivityItem } from '@/lib/api';

interface Props {
  activities: ActivityItem[];
}

export default function RecentActivity({ activities = [] }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-zinc-100">
              Live Telemetry & Audit Stream
            </h2>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Real-time event log across agents and MCP servers
            </p>
          </div>
        </div>
      </div>

      <div className="relative pl-4 border-l border-slate-200 dark:border-zinc-800 space-y-4">
        {activities.map((item) => (
          <div key={item.id} className="relative group">
            <span
              className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full ring-4 ring-white dark:ring-zinc-900 ${
                item.status === 'success'
                  ? 'bg-emerald-500'
                  : item.status === 'warning'
                  ? 'bg-amber-500'
                  : 'bg-indigo-500'
              }`}
            />
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-semibold text-slate-900 dark:text-zinc-100">
                  {item.agent}{' '}
                  <span className="font-normal text-slate-600 dark:text-zinc-400">
                    — {item.action}
                  </span>
                </p>
                <p className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 mt-0.5">
                  {item.target}
                </p>
              </div>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 shrink-0">
                {item.timestamp}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}