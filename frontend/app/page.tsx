'use client';

import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  Bot,
  Server,
  MessageSquare,
  Sun,
  Moon,
  Search,
  Plus,
  Sparkles,
  Terminal,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Send,
  Layers,
  Kanban,
  Command,
  ChevronRight,
  Wifi,
  WifiOff,
  X,
  Play,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import DashboardStats from '@/components/dashboard/DashboardStats';
import AgentStatus from '@/components/dashboard/AgentStatus';
import MCPStatus from '@/components/dashboard/MCPStatus';
import ProjectList from '@/components/dashboard/ProjectList';
import RecentActivity from '@/components/dashboard/RecentActivity';
import {
  INITIAL_PROJECTS,
  INITIAL_AGENTS,
  INITIAL_MCP_SERVERS,
  INITIAL_ACTIVITY,
  INITIAL_MEETINGS,
  Project,
  UserStory,
  AgentInfo,
  MCPServer,
  ActivityItem,
  MeetingRecord,
  checkBackendConnection,
  fetchLiveProjects,
  fetchLiveAgents,
  fetchLiveMCPServers,
  fetchLiveMeetings,
  pingMCPServer,
  dispatchNotification,
  executeAgent,
  aiDecomposeProject,
} from '@/lib/api';

type NavTab = 'overview' | 'projects' | 'agents' | 'mcp' | 'comms';

const KANBAN_COLUMNS: UserStory['status'][] = [
  'Backlog',
  'Ready',
  'In Progress',
  'Testing',
  'Done',
];

export default function SuperMonWorkspace() {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [projects, setProjects] = useState<Project[]>(INITIAL_PROJECTS);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(INITIAL_PROJECTS[0].id);
  const [projectViewMode, setProjectViewMode] = useState<'kanban' | 'tree'>('kanban');
  const [agents, setAgents] = useState<AgentInfo[]>(INITIAL_AGENTS);
  const [mcpServers, setMcpServers] = useState<MCPServer[]>(INITIAL_MCP_SERVERS);
  const [activities, setActivities] = useState<ActivityItem[]>(INITIAL_ACTIVITY);
  const [meetings, setMeetings] = useState<MeetingRecord[]>(INITIAL_MEETINGS);
  const [backendLive, setBackendLive] = useState<boolean>(false);

  // Interactive Terminal & Modals
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    '[SYSTEM] SuperMon Multi-Agent Orchestrator v2.4 initialized.',
    '[MCP-MESH] Connected to 6/6 servers: github, notion, postgresql, redis, slack, whatsapp.',
    '[AGENT:requirements_agent] Standing by for PRD / Epic synthesis.',
    '[AGENT:development_agent] Listening on GitHub webhook events (amogh18t/supermon).',
  ]);

  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState('');
  const [newProjectModal, setNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectRepo, setNewProjectRepo] = useState('amogh18t/');

  const [newStoryModal, setNewStoryModal] = useState(false);
  const [newStoryTitle, setNewStoryTitle] = useState('');
  const [newStoryPoints, setNewStoryPoints] = useState(5);
  const [newStoryPriority, setNewStoryPriority] = useState<UserStory['priority']>('High');

  const [commsChannel, setCommsChannel] = useState<'Slack' | 'WhatsApp'>('Slack');
  const [commsTarget, setCommsTarget] = useState('#eng-supermon');
  const [commsMessage, setCommsMessage] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const selectedProject =
    projects.find((p) => p.id === selectedProjectId) || projects[0] || INITIAL_PROJECTS[0];

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  // Initial load and live telemetry polling
  useEffect(() => {
    const initConnection = async () => {
      const isLive = await checkBackendConnection();
      setBackendLive(isLive);
      if (isLive) {
        const [liveProjects, liveAgents, liveMCP, liveMeetings] = await Promise.all([
          fetchLiveProjects(),
          fetchLiveAgents(),
          fetchLiveMCPServers(),
          fetchLiveMeetings(),
        ]);
        if (liveProjects && liveProjects.length > 0) setProjects(liveProjects);
        if (liveAgents && liveAgents.length > 0) setAgents(liveAgents);
        if (liveMCP && liveMCP.length > 0) setMcpServers(liveMCP);
        if (liveMeetings && liveMeetings.length > 0) setMeetings(liveMeetings);
      }
    };
    initConnection();
  }, []);

  // Keyboard shortcut Cmd/Ctrl + K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setCommandOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Helper to log activity & terminal output
  const pushTelemetry = (
    agentName: string,
    action: string,
    target: string,
    type: ActivityItem['type'] = 'agent',
    status: ActivityItem['status'] = 'success'
  ) => {
    const newAct: ActivityItem = {
      id: `act-${Date.now()}`,
      agent: agentName,
      action,
      target,
      timestamp: 'Just now',
      type,
      status,
    };
    setActivities((prev) => [newAct, ...prev.slice(0, 14)]);
    setTerminalLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] [${agentName.toUpperCase()}] ${action} -> ${target}`,
    ]);
  };

  // Trigger an Agent Run
  const handleTriggerAgent = async (agentId: string) => {
    const targetAgent = agents.find((a) => a.id === agentId);
    if (!targetAgent) return;

    setAgents((prev) =>
      prev.map((a) =>
        a.id === agentId
          ? {
              ...a,
              status: 'Busy',
              current_task: `Executing autonomous pipeline on ${selectedProject.name}...`,
            }
          : a
      )
    );

    pushTelemetry(
      targetAgent.name,
      'Started autonomous workflow execution',
      selectedProject.name,
      'agent',
      'info'
    );
    showToast(`${targetAgent.name} dispatched on ${selectedProject.name}`);

    // Call live backend API if available
    await executeAgent(agentId, selectedProject.id);

    setTimeout(() => {
      setAgents((prev) =>
        prev.map((a) =>
          a.id === agentId
            ? {
                ...a,
                status: 'Online',
                completed_tasks: a.completed_tasks + 1,
                current_task: `Completed run on ${selectedProject.name} • Synced to MCP`,
              }
            : a
        )
      );
      pushTelemetry(
        targetAgent.name,
        'Completed task & persisted state via PostgreSQL + Notion MCP',
        selectedProject.name,
        'agent',
        'success'
      );
    }, 1800);
  };

  // AI Generate Epic & User Stories
  const handleGenerateStories = async (projectId: string) => {
    const targetProj = projects.find((p) => p.id === projectId);
    if (!targetProj) return;

    const generatedStory: UserStory = {
      id: `US-${Math.floor(200 + Math.random() * 700)}`,
      epic_id: targetProj.epics[0]?.id || 'epic-auto',
      title: 'AI-Synthesized Telemetry Circuit Breaker & Slack Alerting',
      description:
        'Automatically generated by Requirements & Planning Agents based on repository analysis.',
      acceptance_criteria: ['Zero-downtime fallback', 'Automated pytest suite'],
      story_points: 5,
      priority: 'High',
      status: 'Ready',
      assigned_agent: 'Development Agent',
    };

    setProjects((prev) =>
      prev.map((p) => {
        if (p.id !== projectId) return p;
        const updatedEpics = p.epics.map((e, idx) =>
          idx === 0 ? { ...e, stories: [generatedStory, ...e.stories] } : e
        );
        return { ...p, epics: updatedEpics, updated_at: 'Just now' };
      })
    );

    pushTelemetry(
      'Planning Agent',
      `Synthesized User Story ${generatedStory.id} (${generatedStory.story_points} pts)`,
      targetProj.name,
      'project',
      'success'
    );
    showToast(`AI generated ${generatedStory.id} in ${targetProj.name}`);

    // Call backend decomposition endpoint
    await aiDecomposeProject(projectId);
  };

  // Move Story across Kanban columns
  const handleAdvanceStoryStatus = (storyId: string, nextStatus: UserStory['status']) => {
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== selectedProject.id) return proj;
        const epics = proj.epics.map((epic) => ({
          ...epic,
          stories: epic.stories.map((st) =>
            st.id === storyId ? { ...st, status: nextStatus } : st
          ),
        }));
        return { ...proj, epics };
      })
    );
    pushTelemetry(
      'Development Agent',
      `Transitioned ${storyId} to [${nextStatus}]`,
      selectedProject.name,
      'project',
      'info'
    );
  };

  // Ping MCP Server
  const handlePingMCP = async (serverId: string) => {
    const result = await pingMCPServer(serverId);
    setMcpServers((prev) =>
      prev.map((s) =>
        s.id === serverId ? { ...s, latency: result.latency, last_sync: 'Just now' } : s
      )
    );
    const server = mcpServers.find((s) => s.id === serverId);
    if (server) {
      pushTelemetry(
        server.name,
        `Health check OK (${result.latency} RTT)`,
        server.endpoint,
        'mcp',
        'success'
      );
      showToast(`${server.name} healthy (${result.latency})`);
    }
  };

  // Convert Meeting Action Item to Agile User Story
  const handleConvertActionItem = (meetingId: string, actionItemId: string, text: string) => {
    const newStory: UserStory = {
      id: `US-${Math.floor(300 + Math.random() * 600)}`,
      epic_id: selectedProject.epics[0]?.id || 'epic-101',
      title: text,
      description: 'Converted directly from Meeting Intelligence Action Item.',
      acceptance_criteria: ['Verified by Testing Agent'],
      story_points: 3,
      priority: 'High',
      status: 'Ready',
      assigned_agent: 'Development Agent',
    };

    setProjects((prev) =>
      prev.map((p) =>
        p.id === selectedProject.id
          ? {
              ...p,
              epics: p.epics.map((e, i) =>
                i === 0 ? { ...e, stories: [newStory, ...e.stories] } : e
              ),
            }
          : p
      )
    );

    setMeetings((prev) =>
      prev.map((m) =>
        m.id === meetingId
          ? {
              ...m,
              action_items: m.action_items.map((ai) =>
                ai.id === actionItemId ? { ...ai, converted: true } : ai
              ),
            }
          : m
      )
    );

    pushTelemetry(
      'Requirements Agent',
      `Converted meeting action item into ${newStory.id}`,
      selectedProject.name,
      'comms',
      'success'
    );
    showToast(`Created ${newStory.id} in ${selectedProject.name} Kanban!`);
  };

  // Create New Project
  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    const created: Project = {
      id: `proj-${Date.now()}`,
      name: newProjectName.trim(),
      description:
        newProjectDesc.trim() ||
        'Autonomous multi-agent software engineering initiative.',
      status: 'Active',
      progress: 10,
      github_repo: newProjectRepo.trim() || 'amogh18t/new-service',
      updated_at: 'Just now',
      epics: [
        {
          id: `epic-${Date.now()}`,
          project_id: `proj-${Date.now()}`,
          title: 'Core Architecture & MVP Scaffolding',
          description: 'Initial Epic generated by Requirements Agent.',
          status: 'In Progress',
          progress: 15,
          stories: [
            {
              id: `US-${Math.floor(100 + Math.random() * 899)}`,
              epic_id: `epic-${Date.now()}`,
              title: 'Initialize Repository, FastAPI Skeleton & CI Pipeline',
              description: 'Bootstrap service with pre-commit hooks and pytest.',
              acceptance_criteria: ['GitHub repo synced', 'CI green'],
              story_points: 5,
              priority: 'Critical',
              status: 'Ready',
              assigned_agent: 'Development Agent',
            },
          ],
        },
      ],
    };

    setProjects((prev) => [created, ...prev]);
    setSelectedProjectId(created.id);
    setNewProjectName('');
    setNewProjectDesc('');
    setNewProjectModal(false);
    setActiveTab('projects');

    pushTelemetry('Requirements Agent', 'Created new project & initial Epic', created.name, 'project', 'success');
    showToast(`Project "${created.name}" initialized!`);
  };

  // Create New User Story
  const handleCreateStory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStoryTitle.trim()) return;

    const story: UserStory = {
      id: `US-${Math.floor(100 + Math.random() * 899)}`,
      epic_id: selectedProject.epics[0]?.id || 'epic-101',
      title: newStoryTitle.trim(),
      description: 'Created via Agile Workspace.',
      acceptance_criteria: ['Unit tests added', 'Code reviewed by Testing Agent'],
      story_points: Number(newStoryPoints) || 5,
      priority: newStoryPriority,
      status: 'Ready',
      assigned_agent: 'Development Agent',
    };

    setProjects((prev) =>
      prev.map((p) =>
        p.id === selectedProject.id
          ? {
              ...p,
              epics: p.epics.map((ep, idx) =>
                idx === 0 ? { ...ep, stories: [story, ...ep.stories] } : ep
              ),
            }
          : p
      )
    );

    setNewStoryTitle('');
    setNewStoryModal(false);
    pushTelemetry('Planning Agent', `Added story ${story.id} to sprint`, selectedProject.name, 'project', 'success');
    showToast(`Added ${story.id} to ${selectedProject.name}`);
  };

  // Send Slack/WhatsApp Dispatch
  const handleSendComms = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commsMessage.trim()) return;

    await dispatchNotification(commsChannel, commsTarget, commsMessage);

    pushTelemetry(
      'Communication Agent',
      `Dispatched ${commsChannel} notification: "${commsMessage.slice(0, 48)}..."`,
      commsTarget,
      'comms',
      'success'
    );
    setCommsMessage('');
    showToast(`Sent via ${commsChannel} MCP to ${commsTarget}`);
  };

  const allSelectedStories = selectedProject.epics.flatMap((e) => e.stories);

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-zinc-950 text-slate-900 dark:text-zinc-100 transition-colors">
      {/* LEFT NAVIGATION SIDEBAR */}
      <aside className="w-64 shrink-0 border-r border-slate-200/80 dark:border-zinc-800/80 bg-white/90 dark:bg-zinc-900/60 backdrop-blur-md flex flex-col justify-between select-none">
        <div>
          {/* Brand Header */}
          <div className="h-16 px-5 flex items-center justify-between border-b border-slate-200/80 dark:border-zinc-800/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/20">
                S
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-sm tracking-tight">SuperMon</span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold">
                    v2.4
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-zinc-400">
                  Agentic SDLC OS
                </p>
              </div>
            </div>
          </div>

          {/* Active Project Quick Switcher */}
          <div className="p-3.5 border-b border-slate-200/80 dark:border-zinc-800/80">
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-zinc-400 mb-1.5">
              Active Workspace
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full text-xs font-medium rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900 px-3 py-2 text-slate-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Primary Nav */}
          <nav className="p-3 space-y-1">
            {[
              { id: 'overview', label: 'Command Center', icon: LayoutDashboard, badge: 'Live' },
              {
                id: 'projects',
                label: 'Projects & Kanban',
                icon: FolderKanban,
                badge: `${allSelectedStories.length}`,
              },
              { id: 'agents', label: 'Agent Studio', icon: Bot, badge: '5' },
              { id: 'mcp', label: 'MCP Server Hub', icon: Server, badge: '6/6' },
              {
                id: 'comms',
                label: 'Comms & Meetings',
                icon: MessageSquare,
                badge: `${meetings.length}`,
              },
            ].map((item) => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as NavTab)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    active
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-zinc-800/70 hover:text-slate-900 dark:hover:text-zinc-100'
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded-md ${
                      active
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: FastAPI Status + Theme Switcher */}
        <div className="p-3.5 border-t border-slate-200/80 dark:border-zinc-800/80 space-y-2.5">
          <div className="rounded-xl p-3 bg-slate-100/80 dark:bg-zinc-900 border border-slate-200/70 dark:border-zinc-800/80">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700 dark:text-zinc-300 flex items-center gap-1.5">
                {backendLive ? (
                  <Wifi className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <WifiOff className="w-3.5 h-3.5 text-amber-500" />
                )}
                FastAPI Engine
              </span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  backendLive
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold'
                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                }`}
              >
                {backendLive ? 'Port 8000 Live' : 'Interactive Sim'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-1">
              6 MCP Bridges Ready • 0 Queue Lag
            </p>
          </div>

          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900 text-xs font-medium text-slate-700 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <span className="flex items-center gap-2">
              {theme === 'dark' ? (
                <Moon className="w-4 h-4 text-indigo-400" />
              ) : (
                <Sun className="w-4 h-4 text-amber-500" />
              )}
              {theme === 'dark' ? 'Dark Mode Active' : 'Light Mode Active'}
            </span>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-200 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400">
              Switch
            </span>
          </button>
        </div>
      </aside>

      {/* MAIN WORKSPACE CONTENT */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* STICKY TOPBAR */}
        <header className="h-16 px-6 sticky top-0 z-20 border-b border-slate-200/80 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400">
            <span className="font-medium text-slate-900 dark:text-zinc-100">SuperMon</span>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="capitalize font-medium text-indigo-600 dark:text-indigo-400">
              {activeTab}
            </span>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="truncate max-w-[220px] font-medium text-slate-800 dark:text-zinc-200">
              {selectedProject.name}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Command Palette Trigger */}
            <button
              onClick={() => setCommandOpen(true)}
              className="flex items-center gap-3 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900 text-xs text-slate-500 dark:text-zinc-400 hover:border-indigo-500/40 transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search or run agent command...</span>
              <kbd className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 text-slate-500">
                ⌘K
              </kbd>
            </button>

            {/* Quick Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              title="Toggle Dark/Light Mode"
              className="p-2 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-100 transition-colors"
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-slate-700" />
              )}
            </button>

            {/* Primary Action */}
            <button
              onClick={() => setNewProjectModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              New Project
            </button>
          </div>
        </header>

        {/* WORKSPACE BODY */}
        <main className="flex-1 p-6 space-y-6 max-w-[1600px] w-full mx-auto">
          {/* TAB 1: OVERVIEW COMMAND CENTER */}
          {activeTab === 'overview' && (
            <>
              <DashboardStats
                projects={projects}
                agents={agents}
                mcpServers={mcpServers}
                onNavigate={(tab) => setActiveTab(tab as NavTab)}
              />

              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
                <div className="xl:col-span-7 space-y-6">
                  <ProjectList
                    projects={projects}
                    onSelectProject={(proj) => {
                      setSelectedProjectId(proj.id);
                      setActiveTab('projects');
                    }}
                    onNewProject={() => setNewProjectModal(true)}
                    onGenerateStories={handleGenerateStories}
                  />
                  <MCPStatus servers={mcpServers} onPingServer={handlePingMCP} />
                </div>

                <div className="xl:col-span-5 space-y-6">
                  <AgentStatus
                    agents={agents}
                    onTriggerAgent={handleTriggerAgent}
                    onInspectAgent={() => setActiveTab('agents')}
                  />
                  <RecentActivity activities={activities} />
                </div>
              </div>
            </>
          )}

          {/* TAB 2: AGILE KANBAN & EPIC HIERARCHY */}
          {activeTab === 'projects' && (
            <div className="space-y-6">
              {/* Project Header Controls */}
              <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h1 className="text-lg font-bold text-slate-900 dark:text-zinc-50">
                      {selectedProject.name}
                    </h1>
                    <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold">
                      {selectedProject.github_repo}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                    {selectedProject.description}
                  </p>
                </div>

                <div className="flex items-center gap-2.5 flex-wrap">
                  <div className="inline-flex rounded-xl p-1 bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700">
                    <button
                      onClick={() => setProjectViewMode('kanban')}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        projectViewMode === 'kanban'
                          ? 'bg-white dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 shadow-sm'
                          : 'text-slate-600 dark:text-zinc-400'
                      }`}
                    >
                      <Kanban className="w-3.5 h-3.5" />
                      Kanban Board
                    </button>
                    <button
                      onClick={() => setProjectViewMode('tree')}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        projectViewMode === 'tree'
                          ? 'bg-white dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 shadow-sm'
                          : 'text-slate-600 dark:text-zinc-400'
                      }`}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      Epic Hierarchy
                    </button>
                  </div>

                  <button
                    onClick={() => handleGenerateStories(selectedProject.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-indigo-500/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/10 text-xs font-medium transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Generate Stories
                  </button>
                  <button
                    onClick={() => setNewStoryModal(true)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Story
                  </button>
                </div>
              </div>

              {/* KANBAN VIEW */}
              {projectViewMode === 'kanban' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
                  {KANBAN_COLUMNS.map((colStatus) => {
                    const colStories = allSelectedStories.filter(
                      (s) => s.status === colStatus
                    );
                    const totalPts = colStories.reduce((a, s) => a + s.story_points, 0);

                    return (
                      <div
                        key={colStatus}
                        className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-slate-100/60 dark:bg-zinc-900/30 p-3.5 flex flex-col min-h-[480px]"
                      >
                        <div className="flex items-center justify-between mb-3 px-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-800 dark:text-zinc-200">
                              {colStatus}
                            </span>
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-white dark:bg-zinc-800 text-slate-600 dark:text-zinc-400 font-semibold border border-slate-200 dark:border-zinc-700">
                              {colStories.length}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-500 dark:text-zinc-400">
                            {totalPts} pts
                          </span>
                        </div>

                        <div className="space-y-3 flex-1">
                          {colStories.map((story) => {
                            const nextIdx =
                              (KANBAN_COLUMNS.indexOf(story.status) + 1) %
                              KANBAN_COLUMNS.length;
                            const nextStatus = KANBAN_COLUMNS[nextIdx];

                            return (
                              <div
                                key={story.id}
                                className="rounded-xl border border-slate-200/90 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3.5 shadow-sm hover:border-indigo-500/40 transition-all flex flex-col justify-between gap-3"
                              >
                                <div>
                                  <div className="flex items-center justify-between gap-2">
                                    <span className="text-[11px] font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                                      {story.id}
                                    </span>
                                    <span
                                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                        story.priority === 'Critical'
                                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                                          : story.priority === 'High'
                                          ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                                          : 'bg-sky-500/10 text-sky-600 dark:text-sky-400'
                                      }`}
                                    >
                                      {story.priority}
                                    </span>
                                  </div>
                                  <h4 className="font-semibold text-xs text-slate-900 dark:text-zinc-100 mt-1.5 leading-snug">
                                    {story.title}
                                  </h4>
                                  <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-1 line-clamp-2">
                                    {story.description}
                                  </p>
                                </div>

                                <div className="pt-2.5 border-t border-slate-100 dark:border-zinc-800/80 flex items-center justify-between text-xs">
                                  <span className="font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400 text-[10px]">
                                    {story.story_points} pts
                                  </span>
                                  <button
                                    onClick={() =>
                                      handleAdvanceStoryStatus(story.id, nextStatus)
                                    }
                                    className="inline-flex items-center gap-1 text-[11px] font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                                  >
                                    Move to {nextStatus}
                                    <ArrowRight className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                /* EPIC HIERARCHY TREE VIEW */
                <div className="space-y-4">
                  {selectedProject.epics.map((epic) => (
                    <div
                      key={epic.id}
                      className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                            {epic.id.toUpperCase()}
                          </span>
                          <h3 className="text-base font-bold text-slate-900 dark:text-zinc-100">
                            {epic.title}
                          </h3>
                          <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
                            {epic.description}
                          </p>
                        </div>
                        <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold">
                          {epic.stories.length} Stories
                        </span>
                      </div>

                      <div className="mt-4 divide-y divide-slate-200/60 dark:divide-zinc-800">
                        {epic.stories.map((st) => (
                          <div
                            key={st.id}
                            className="py-3 flex items-center justify-between gap-4 text-xs"
                          >
                            <div className="flex items-center gap-3">
                              <span className="font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                                {st.id}
                              </span>
                              <span className="font-medium text-slate-900 dark:text-zinc-100">
                                {st.title}
                              </span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-500 dark:text-zinc-400">
                                {st.assigned_agent}
                              </span>
                              <span className="font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400">
                                {st.story_points} pts
                              </span>
                              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium">
                                {st.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MULTI-AGENT STUDIO & LIVE EXECUTION TERMINAL */}
          {activeTab === 'agents' && (
            <div className="space-y-6">
              {/* Visual SDLC Pipeline Bar */}
              <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400 mb-4">
                  Autonomous SDLC Agent Handoff Pipeline
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {agents.map((ag, index) => (
                    <div
                      key={ag.id}
                      className="rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50/70 dark:bg-zinc-900/40 p-3.5 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                            STAGE 0{index + 1}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                            {ag.success_rate}% SLA
                          </span>
                        </div>
                        <h3 className="font-bold text-sm text-slate-900 dark:text-zinc-100 mt-1.5">
                          {ag.name}
                        </h3>
                        <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                          {ag.role}
                        </p>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-zinc-800 flex items-center justify-between text-xs">
                        <span className="text-[11px] font-mono text-slate-500">
                          {ag.completed_tasks} runs
                        </span>
                        <button
                          onClick={() => handleTriggerAgent(ag.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors shadow-sm"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          Execute
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Live Streaming Execution Console */}
              <div className="rounded-2xl border border-slate-800 bg-zinc-950 text-zinc-100 p-5 shadow-lg">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-mono font-semibold text-zinc-200">
                      supermon://agent-runtime-stream (MCP Tool Call Trace)
                    </span>
                  </div>
                  <button
                    onClick={() =>
                      handleTriggerAgent(
                        agents[Math.floor(Math.random() * agents.length)].id
                      )
                    }
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-colors shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Simulate Full Pipeline Step
                  </button>
                </div>
                <div className="font-mono text-xs space-y-1.5 max-h-80 overflow-y-auto">
                  {terminalLogs.map((log, i) => (
                    <div key={i} className="text-zinc-300 leading-relaxed">
                      <span className="text-emerald-400 mr-2">$</span>
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: MCP SERVER HUB */}
          {activeTab === 'mcp' && (
            <div className="space-y-6">
              <MCPStatus servers={mcpServers} onPingServer={handlePingMCP} />
            </div>
          )}

          {/* TAB 5: COMMS & MEETING INTELLIGENCE */}
          {activeTab === 'comms' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Meeting Intelligence & Action Item Converter */}
              <div className="lg:col-span-7 space-y-4">
                <div className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm">
                  <h2 className="text-base font-bold text-slate-900 dark:text-zinc-100">
                    AI Meeting Intelligence & Action Item Converter
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
                    Convert extracted standup and architecture action items into Agile User Stories with 1-click
                  </p>

                  <div className="mt-4 space-y-4">
                    {meetings.map((mtg) => (
                      <div
                        key={mtg.id}
                        className="rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50/60 dark:bg-zinc-900/40 p-4"
                      >
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-sm text-slate-900 dark:text-zinc-100">
                            {mtg.title}
                          </h3>
                          <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold">
                            {mtg.channel} • {mtg.date}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-zinc-300 mt-2">
                          {mtg.summary}
                        </p>

                        <div className="mt-3 pt-3 border-t border-slate-200/70 dark:border-zinc-800 space-y-2">
                          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                            Extracted Action Items
                          </p>
                          {mtg.action_items.map((ai) => (
                            <div
                              key={ai.id}
                              className="flex items-center justify-between gap-3 bg-white dark:bg-zinc-900 p-2.5 rounded-lg border border-slate-200/60 dark:border-zinc-800 text-xs"
                            >
                              <div>
                                <p className="font-medium text-slate-800 dark:text-zinc-200">
                                  {ai.text}
                                </p>
                                <span className="text-[11px] text-slate-400">
                                  Assignee: {ai.assignee}
                                </span>
                              </div>

                              {ai.converted ? (
                                <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold shrink-0">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  In Kanban
                                </span>
                              ) : (
                                <button
                                  onClick={() =>
                                    handleConvertActionItem(mtg.id, ai.id, ai.text)
                                  }
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shrink-0 shadow-sm transition-colors"
                                >
                                  <Sparkles className="w-3 h-3" />
                                  Convert to Story
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Slack & WhatsApp MCP Dispatcher */}
              <div className="lg:col-span-5">
                <form
                  onSubmit={handleSendComms}
                  className="rounded-2xl border border-slate-200/80 dark:border-zinc-800/80 bg-white dark:bg-zinc-900/60 p-5 shadow-sm space-y-4"
                >
                  <h2 className="text-base font-bold text-slate-900 dark:text-zinc-100">
                    MCP Notification Dispatcher
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-zinc-400">
                    Broadcast standup digests or alerts via Slack MCP or WhatsApp MCP
                  </p>

                  <div className="grid grid-cols-2 gap-2">
                    {(['Slack', 'WhatsApp'] as const).map((ch) => (
                      <button
                        type="button"
                        key={ch}
                        onClick={() => {
                          setCommsChannel(ch);
                          setCommsTarget(
                            ch === 'Slack' ? '#eng-supermon' : '+91-Team-Lead'
                          );
                        }}
                        className={`py-2 rounded-xl text-xs font-semibold border transition-all ${
                          commsChannel === ch
                            ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                            : 'border-slate-200 dark:border-zinc-800 text-slate-700 dark:text-zinc-300 hover:bg-slate-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        {ch} MCP
                      </button>
                    ))}
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Destination Channel / Recipient
                    </label>
                    <input
                      value={commsTarget}
                      onChange={(e) => setCommsTarget(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900 px-3 py-2 text-xs text-slate-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Message Payload
                    </label>
                    <textarea
                      rows={4}
                      value={commsMessage}
                      onChange={(e) => setCommsMessage(e.target.value)}
                      placeholder="e.g., Sprint 14 velocity check complete. All 42 pytest assertions passed."
                      className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900 p-3 text-xs text-slate-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Dispatch via {commsChannel} MCP
                  </button>
                </form>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* GLOBAL COMMAND PALETTE (Cmd/Ctrl + K) */}
      {commandOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-24 px-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-2xl overflow-hidden">
            <div className="flex items-center px-4 border-b border-slate-200 dark:border-zinc-800">
              <Command className="w-4 h-4 text-slate-400 mr-2.5" />
              <input
                autoFocus
                value={commandQuery}
                onChange={(e) => setCommandQuery(e.target.value)}
                placeholder="Type a command (e.g., 'toggle theme', 'run dev agent', 'kanban')..."
                className="w-full py-3.5 text-sm bg-transparent focus:outline-none text-slate-900 dark:text-zinc-100"
              />
              <button
                onClick={() => setCommandOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-2 max-h-72 overflow-y-auto space-y-1 text-xs">
              {[
                {
                  label: `Toggle ${theme === 'dark' ? 'Light' : 'Dark'} Mode`,
                  action: () => toggleTheme(),
                },
                {
                  label: 'Go to Agile Kanban & Epic Workspace',
                  action: () => setActiveTab('projects'),
                },
                {
                  label: 'Open Multi-Agent Studio & Live Terminal',
                  action: () => setActiveTab('agents'),
                },
                {
                  label: 'AI-Generate User Stories for Active Project',
                  action: () => handleGenerateStories(selectedProject.id),
                },
                {
                  label: 'Trigger Development Agent Run',
                  action: () => handleTriggerAgent('development_agent'),
                },
                {
                  label: 'Ping All 6 MCP Servers',
                  action: () => mcpServers.forEach((m) => handlePingMCP(m.id)),
                },
              ]
                .filter((item) =>
                  item.label.toLowerCase().includes(commandQuery.toLowerCase())
                )
                .map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      cmd.action();
                      setCommandOpen(false);
                    }}
                    className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-indigo-600 hover:text-white flex items-center justify-between transition-colors text-slate-700 dark:text-zinc-300"
                  >
                    <span>{cmd.label}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* NEW PROJECT MODAL */}
      {newProjectModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateProject}
            className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-2xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-zinc-100">
                Initialize SDLC Project
              </h3>
              <button
                type="button"
                onClick={() => setNewProjectModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Project Name</label>
              <input
                required
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="e.g., Autonomous Maritime Risk Engine"
                className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">GitHub Repository</label>
              <input
                value={newProjectRepo}
                onChange={(e) => setNewProjectRepo(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">
                High-Level PRD / Description
              </label>
              <textarea
                rows={3}
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                placeholder="Requirements Agent will automatically decompose this into Epics..."
                className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 p-3 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setNewProjectModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 text-xs font-medium hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                Create & Seed Epics
              </button>
            </div>
          </form>
        </div>
      )}

      {/* NEW USER STORY MODAL */}
      {newStoryModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateStory}
            className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-2xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-zinc-100">
                Add Agile User Story
              </h3>
              <button
                type="button"
                onClick={() => setNewStoryModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">User Story Title</label>
              <input
                required
                value={newStoryTitle}
                onChange={(e) => setNewStoryTitle(e.target.value)}
                placeholder="As an engineer, I want..."
                className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Story Points</label>
                <input
                  type="number"
                  value={newStoryPoints}
                  onChange={(e) => setNewStoryPoints(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-1">Priority</label>
                <select
                  value={newStoryPriority}
                  onChange={(e) =>
                    setNewStoryPriority(e.target.value as UserStory['priority'])
                  }
                  className="w-full rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setNewStoryModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 text-xs font-medium hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                Add to Kanban
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TOAST NOTIFICATION */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-xl border border-slate-800 text-xs font-medium animate-bounce">
          <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
          {toast}
        </div>
      )}
    </div>
  );
}