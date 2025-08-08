import React from 'react';

interface DashboardStatsProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  trend?: string;
  trendDirection?: 'up' | 'down';
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ title, value, icon: Icon, color, trend, trendDirection }) => {
  const colorClasses = {
    primary: 'text-primary-600 bg-primary-100',
    secondary: 'text-secondary-600 bg-secondary-100',
    success: 'text-success-600 bg-success-100',
    warning: 'text-warning-600 bg-warning-100',
  };

  const trendColor = trendDirection === 'up' ? 'text-success-600' : 'text-error-600';

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex flex-col space-y-2">
          <div className="text-sm font-medium text-gray-500">{title}</div>
          <div className="text-3xl font-bold text-gray-900">{value}</div>
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center space-x-1">
          <span className={`text-sm font-medium ${trendColor}`}>{trend}</span>
          <span className="text-sm text-gray-500">vs last month</span>
        </div>
      )}
    </div>
  );
};