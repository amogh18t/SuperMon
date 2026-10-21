'use client';

import React from 'react';
import { FolderGit2, GitBranch, Plus, Sparkles, ChevronRight } from 'lucide-react';
import { Project } from '@/lib/api';

interface Props {
  projects: Project[];
  onSelectProject?: (project: Project) => void;
  onNewProject?: () => void;
  onGenerateStories?: (projectId: string) => void;
}

export default function ProjectList({
  projects = [],
  onSelectProject,
  onNewProject,
  onGenerateStories,
}: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
            <FolderGit2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-zinc-100">
              Active SDLC Projects
            </h2>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Click any project to open its Agile Kanban & Epic hierarchy
            </p>
          </div>
        </div>

        <button
          onClick={onNewProject}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          New Project
        </button>
      </div>

      <div className="space-y-3">
        {projects.map((project) => {
          const storyCount = project.epics.reduce((a, e) => a + e.stories.length, 0);
          return (
            <div
              key={project.id}
              className="group rounded-xl border border-slate-200/70 dark:border-zinc-800/80 bg-slate-50/60 dark:bg-zinc-900/40 p-4 hover:border-indigo-500/30 transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div
                  onClick={() => onSelectProject?.(project)}
                  className="cursor-pointer flex-1 min-w-0"
                >
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-semibold text-sm text-slate-900 dark:text-zinc-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {project.name}
                    </h3>
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                      {project.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1 line-clamp-1">
                    {project.description}
                  </p>
                  <div className="flex items-center gap-4 mt-2.5 text-xs text-slate-500 dark:text-zinc-400">
                    <span className="inline-flex items-center gap-1 font-mono">
                      <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                      {project.github_repo}
                    </span>
                    <span>{project.epics.length} Epics</span>
                    <span>{storyCount} User Stories</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => onGenerateStories?.(project.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-indigo-500/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/10 text-xs font-medium transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Decompose
                  </button>
                  <button
                    onClick={() => onSelectProject?.(project)}
                    className="p-1.5 rounded-lg border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-100"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-500 dark:text-zinc-400">Sprint Completion</span>
                  <span className="font-mono font-semibold text-slate-700 dark:text-zinc-200">
                    {project.progress}%
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}