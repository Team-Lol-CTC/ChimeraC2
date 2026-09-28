// MOCK — Saliha will replace this with the real AgentTable.
// Props contract:
//   agents:          Agent[]
//   selectedAgentId: string | null
//   onSelectAgent:   (agentId: string) => void

const OS_BADGE = {
  linux: 'bg-yellow-900 text-yellow-200 border-yellow-700',
  windows: 'bg-blue-900 text-blue-200 border-blue-700',
  darwin: 'bg-purple-900 text-purple-200 border-purple-700',
};

export default function AgentTable({
  agents = [],
  selectedAgentId = null,
  onSelectAgent = () => {},
}) {
  if (agents.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500 py-12">
        No agents registered yet…
      </div>
    );
  }

  return (
    <table className="w-full text-sm">
      <thead className="bg-gray-950 text-gray-400 text-xs uppercase tracking-wider">
        <tr>
          <th className="text-left px-4 py-2 font-medium">Host</th>
          <th className="text-left px-4 py-2 font-medium">OS</th>
          <th className="text-left px-4 py-2 font-medium">User</th>
          <th className="text-left px-4 py-2 font-medium">IP</th>
          <th className="text-left px-4 py-2 font-medium">Last Seen</th>
        </tr>
      </thead>
      <tbody>
        {agents.map((agent) => {
          const isSelected = agent.agent_id === selectedAgentId;
          const badge =
            OS_BADGE[agent.os?.toLowerCase()] ||
            'bg-gray-800 text-gray-300 border-gray-700';

          return (
            <tr
              key={agent.agent_id}
              onClick={() => onSelectAgent(agent.agent_id)}
              className={`cursor-pointer border-t border-gray-800 transition-colors ${
                isSelected
                  ? 'bg-gray-800'
                  : 'hover:bg-gray-900/80'
              }`}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  <div>
                    <div className="font-medium text-gray-100">
                      {agent.hostname}
                    </div>
                    <div className="text-xs text-gray-500 font-mono">
                      {agent.agent_id}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded border ${badge}`}
                >
                  {agent.os || 'unknown'}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-300">{agent.user}</td>
              <td className="px-4 py-3 text-gray-400 font-mono text-xs">
                {agent.ip}
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs">
                {agent.last_check_in
                  ? new Date(agent.last_check_in).toLocaleTimeString()
                  : '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
