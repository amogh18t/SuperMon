import React from 'react';

interface AgentStatusProps {
  status: any;
  isLoading: boolean;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({ status, isLoading }) => {
  if (isLoading) {
    return <div className="card"><p>Loading Agent Status...</p></div>;
  }

  return (
    <div className="card">
      <ul className="space-y-2">
        {status && status.agents && Object.entries(status.agents).map(([agentName, agentData]: [string, any]) => (
          <li key={agentName} className="flex items-center justify-between text-sm">
            <span className="capitalize text-gray-700">{agentName}</span>
            {agentData.initialized ? (
              <span className="badge-success">Active</span>
            ) : (
              <span className="badge-error">Inactive</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};