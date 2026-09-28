import { useState } from 'react';
import { useC2Stream } from './hooks/useC2Stream';
import AgentTable from './components/AgentTable';
import TerminalConsole from './components/TerminalConsole';

export default function App() {
  const { agents, terminalOutput, sendCommand, status } = useC2Stream();
  const [selectedAgentId, setSelectedAgentId] = useState(null);

  const selectedAgent = agents.find((a) => a.agent_id === selectedAgentId) || null;

  const handleSend = (command) => {
    if (!selectedAgentId) return false;
    return sendCommand(selectedAgentId, command);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">ChimeraC2</h1>
          <p className="text-xs text-gray-500">Mission Control</p>
        </div>
        <ConnectionStatus status={status} />
      </header>

      {/* Body */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 overflow-hidden">
        {/* Left: Agent fleet */}
        <section className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
          <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-300">Agent Fleet</h2>
            <span className="text-xs text-gray-500">{agents.length} active</span>
          </div>
          <AgentTable
            agents={agents}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
          />
        </section>

        {/* Right: Terminal */}
        <section className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
          <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-300">
              Terminal {selectedAgent && `— ${selectedAgent.hostname}`}
            </h2>
            {selectedAgent && (
              <span className="text-xs text-gray-500">
                {selectedAgent.agent_id}
              </span>
            )}
          </div>
          <TerminalConsole
            output={terminalOutput}
            selectedAgent={selectedAgent}
            onSend={handleSend}
          />
        </section>
      </main>
    </div>
  );
}

function ConnectionStatus({ status }) {
  const color =
    status === 'open'
      ? 'bg-green-500'
      : status === 'connecting'
      ? 'bg-yellow-500 animate-pulse'
      : 'bg-red-500';

  const label =
    status === 'open'
      ? 'Connected'
      : status === 'connecting'
      ? 'Connecting…'
      : 'Disconnected';

  return (
    <div className="flex items-center gap-2 text-xs text-gray-400">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      {label}
    </div>
  );
}
