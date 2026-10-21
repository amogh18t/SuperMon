'use client';

import React from 'react';
import { FolderKanban, Bot, Server, CheckCircle2, ArrowUpRight } from 'lucide-react';
import { Project, AgentInfo, MCPServer } from '@/lib/api';

interface Props {
  projects: Project[];
  agents: AgentInfo[];
  mcpServers: MCPServer[];
  onNavigate?: (tab: string) => void;
}

export default function DashboardStats({
  projects = [],
  agents = [],
  mcpServers = [],
  onNavigate,
}: Props) {
  const totalStories = projects.reduce(
    (acc, p) => acc + p.epics.reduce((eAcc, e) => eAcc + e.stories.length, 0),
    0
  );
  const doneStories = projects.reduce(
    (acc, p) =>
      acc +
      p.epics.reduce(
        (eAcc, e) => eAcc + e.stories.filter((s) => s.status === 'Done').length,
        0
      ),
    0
  );

  const activeAgents = agents.filter((a) => a.status === 'Online' || a.status === 'Busy').length;
  const connectedMCPs = mcpServers.filter((m) => m.status === 'Connected').length;

  const cards = [
    {
      title: 'Active Projects & Epics',
      value: `${projects.length} Projects`,
      sub: `${projects.reduce((a, p) => a + p.epics.length, 0)} Epics tracked in DAG`,
      trend: '+14% velocity',
      icon: FolderKanban,
      color: 'from-indigo-500/15 to-violet-500/5 text-indigo-600 dark:text-indigo-400 border-indigo-500/20',
      tab: 'projects',
    },
    {
      title: 'Autonomous Agents',
      value: `${activeAgents} / ${agents.length} Active`,
      sub: `${agents.reduce((a, ag) => a + ag.completed_tasks, 0)} tasks executed`,
      trend: '98.8% success',
      icon: Bot,
      color: 'from-emerald-500/15 to-teal-500/5 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
      tab: 'agents',
    },
    {
      title: 'MCP Server Mesh',
      value: `${connectedMCPs} / ${mcpServers.length} Online`,
      sub: `${mcpServers.reduce((a, m) => a + m.active_tools, 0)} MCP tools exposed`,
      trend: '28ms avg ping',
      icon: Server,
      color: 'from-sky-500/15 to-cyan-500/5 text-sky-600 dark:text-sky-400 border-sky-500/20',
      tab: 'mcp',
    },
    {
      title: 'Sprint Story Completion',
      value: `${doneStories} / ${totalStories || 1} Stories`,
      sub: 'Auto-verified via Testing Agent',
      trend: 'On schedule',
      icon: CheckCircle2,
      color: 'from-amber-500/15 to-orange-500/5 text-amber-600 dark:text-amber-400 border-amber-500/20',
      tab: 'projects',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            onClick={() => onNavigate?.(card.tab)}
            className="group cursor-pointer rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 hover:border-indigo-500/40 dark:hover:border-indigo-500/40 transition-all duration-200 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div className={`p-2.5 rounded-xl bg-gradient-to-br border ${card.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-300">
                {card.trend}
                <ArrowUpRight className="w-3.5 h-3.5" />
              </span>
            </div>
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-zinc-400">
                {card.title}
              </p>
              <h3 className="text-2xl font-bold mt-1 text-slate-900 dark:text-zinc-50">
                {card.value}
              </h3>
              <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">{card.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}