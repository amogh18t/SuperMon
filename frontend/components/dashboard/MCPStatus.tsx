import React from 'react';

interface MCPStatusProps {
  status: any;
  isLoading: boolean;
}

export const MCPStatus: React.FC<MCPStatusProps> = ({ status, isLoading }) => {
  if (isLoading) {
    return <div className="card"><p>Loading MCP Status...</p></div>;
  }

  return (
    <div className="card">
       <ul className="space-y-2">
        {status && status.connections && Object.entries(status.connections).map(([connName, connDetails]: [string, any]) => (
          <li key={connName} className="flex items-center justify-between text-sm">
            <span className="capitalize text-gray-700">{connName}</span>
            {connDetails.status === 'connected' ? (
              <span className="badge-success">Connected</span>
            ) : (
              <span className="badge-error">Error</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};