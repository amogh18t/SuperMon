'use client';

import React from 'react';
import { useQuery } from 'react-query';
import { 
  ChartBarIcon, 
  FolderIcon, 
  UserGroupIcon, 
  CalendarIcon,
  CogIcon,
  RocketLaunchIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

import { api } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { ProjectList } from '@/components/dashboard/ProjectList';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { AgentStatus } from '@/components/dashboard/AgentStatus';
import { MCPStatus } from '@/components/dashboard/MCPStatus';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery('dashboard-stats', 
    () => api.get('/projects/status').then(res => res.data),
    { refetchInterval: 30000 }
  );

  const { data: projects, isLoading: projectsLoading } = useQuery('projects', 
    () => api.get('/projects').then(res => res.data),
    { refetchInterval: 60000 }
  );

  const { data: agentStatus, isLoading: agentStatusLoading } = useQuery('agent-status',
    () => api.get('/agents/status').then(res => res.data),
    { refetchInterval: 10000 }
  );

  const { data: mcpStatus, isLoading: mcpStatusLoading } = useQuery('mcp-status',
    () => api.get('/communication/mcp-status').then(res => res.data),
    { refetchInterval: 15000 }
  );

  if (statsLoading || projectsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <RocketLaunchIcon className="h-8 w-8 text-primary-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">SuperMon</h1>
              <span className="ml-2 text-sm text-gray-500">SDLC Automation Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="btn-secondary">
                <CogIcon className="h-5 w-5 mr-2" />
                Settings
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to SuperMon
          </h2>
          <p className="text-gray-600 text-lg">
            Your AI-powered SDLC automation platform is ready to streamline your development process.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <DashboardStats
            title="Active Projects"
            value={stats?.total_projects || 0}
            icon={FolderIcon}
            color="primary"
            trend="+12%"
            trendDirection="up"
          />
          <DashboardStats
            title="Total Epics"
            value={stats?.total_epics || 0}
            icon={ChartBarIcon}
            color="secondary"
            trend="+8%"
            trendDirection="up"
          />
          <DashboardStats
            title="User Stories"
            value={stats?.total_stories || 0}
            icon={DocumentTextIcon}
            color="success"
            trend="+15%"
            trendDirection="up"
          />
          <DashboardStats
            title="Team Members"
            value={stats?.total_team_members || 0}
            icon={UserGroupIcon}
            color="warning"
            trend="+3"
            trendDirection="up"
          />
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Projects and Activity */}
          <div className="lg:col-span-2 space-y-8">
            {/* Projects */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Active Projects</h3>
                <button className="btn-primary">
                  <FolderIcon className="h-4 w-4 mr-2" />
                  New Project
                </button>
              </div>
              <ProjectList projects={projects || []} />
            </motion.div>

            {/* Recent Activity */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <RecentActivity />
            </motion.div>
          </div>

          {/* Right Column - Status and Quick Actions */}
          <div className="space-y-8">
            {/* Agent Status */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Agents Status</h3>
              <AgentStatus status={agentStatus} isLoading={agentStatusLoading} />
            </motion.div>

            {/* MCP Connections */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">MCP Connections</h3>
              <MCPStatus status={mcpStatus} isLoading={mcpStatusLoading} />
            </motion.div>

            {/* Quick Actions */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="card"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full btn-primary">
                  <ChatBubbleLeftRightIcon className="h-4 w-4 mr-2" />
                  Analyze Conversations
                </button>
                <button className="w-full btn-secondary">
                  <CalendarIcon className="h-4 w-4 mr-2" />
                  Schedule Meeting
                </button>
                <button className="w-full btn-secondary">
                  <DocumentTextIcon className="h-4 w-4 mr-2" />
                  Generate Documentation
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
} 