'use client';

import React from 'react';
import { Server, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';
import { MCPServer } from '@/lib/api';

interface Props {
  servers: MCPServer[];
  onPingServer?: (id: string) => void;
}

export default function MCPStatus({ servers = [], onPingServer }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-zinc-100">
              MCP Server Mesh
            </h2>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Model Context Protocol bridges (GitHub, Notion, PG, Redis, Slack, WhatsApp)
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {servers.map((mcp) => (
          <div
            key={mcp.id}
            className="rounded-xl border border-slate-200/70 dark:border-zinc-800/80 bg-slate-50/60 dark:bg-zinc-900/40 p-3.5 hover:border-sky-500/30 transition-all"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-slate-900 dark:text-zinc-100">
                  {mcp.name}
                </span>
                <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${
                  mcp.status === 'Connected'
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                }`}>
                  {mcp.status === 'Connected' ? (
                    <CheckCircle2 className="w-3 h-3" />
                  ) : (
                    <AlertTriangle className="w-3 h-3" />
                  )}
                  {mcp.status}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-0.5">
                {mcp.category} • {mcp.active_tools} tools
              </p>
              <p className="text-[11px] font-mono text-slate-400 dark:text-zinc-500 mt-1 truncate">
                {mcp.endpoint}
              </p>
            </div>

            <div className="mt-3 pt-2.5 border-t border-slate-200/60 dark:border-zinc-800/80 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                  {mcp.latency}
                </span>
                <span className="text-slate-400 dark:text-zinc-500">Sync {mcp.last_sync}</span>
              </div>
              <button
                onClick={() => onPingServer?.(mcp.id)}
                className="inline-flex items-center gap-1 text-xs font-medium text-sky-600 dark:text-sky-400 hover:underline"
              >
                <RefreshCw className="w-3 h-3" />
                Ping
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}