'use client';

import React from 'react';
import { Bot, Play, Terminal, Sparkles } from 'lucide-react';
import { AgentInfo } from '@/lib/api';

interface Props {
  agents: AgentInfo[];
  onTriggerAgent?: (agentId: string) => void;
  onInspectAgent?: (agent: AgentInfo) => void;
}

export default function AgentStatus({ agents = [], onTriggerAgent, onInspectAgent }: Props) {
  const statusBadge = (status: AgentInfo['status']) => {
    switch (status) {
      case 'Online':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'Busy':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'Error':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-500/10 text-slate-600 dark:text-zinc-400 border-slate-500/20';
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-zinc-100">
              Multi-Agent Workforce
            </h2>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              5 specialized SDLC agents with autonomous MCP tool access
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="group rounded-xl border border-slate-200/70 dark:border-zinc-800/80 bg-slate-50/60 dark:bg-zinc-900/40 p-3.5 hover:border-indigo-500/30 transition-all"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-sm text-slate-900 dark:text-zinc-100">
                    {agent.name}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full border ${statusBadge(
                      agent.status
                    )}`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === 'Busy'
                          ? 'bg-amber-500 animate-ping'
                          : agent.status === 'Online'
                          ? 'bg-emerald-500'
                          : 'bg-rose-500'
                      }`}
                    />
                    {agent.status}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400 dark:text-zinc-500">
                    {agent.avg_latency}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">{agent.role}</p>
                <div className="mt-2 flex items-center gap-2 text-xs font-mono text-slate-600 dark:text-zinc-300 bg-white/70 dark:bg-zinc-800/50 p-1.5 rounded-lg border border-slate-200/50 dark:border-zinc-800">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <span className="truncate">{agent.current_task}</span>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => onInspectAgent?.(agent)}
                  title="Inspect Agent Logs"
                  className="p-2 rounded-lg border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-slate-600 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                >
                  <Terminal className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onTriggerAgent?.(agent.id)}
                  title="Dispatch Agent Run"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors shadow-sm"
                >
                  <Play className="w-3 h-3 fill-current" />
                  Run
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}