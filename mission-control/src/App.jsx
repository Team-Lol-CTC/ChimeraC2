import { useState } from 'react';
import { useC2Stream } from './hooks/useC2Stream';
import AgentTable from './components/AgentTable';
import TerminalConsole from './components/TerminalConsole';

export default function App() {
  const { agents, terminalOutput, sendCommand, status } = useC2Stream();
  const [selectedAgentId, setSelectedAgentId] = useState(null);

  const selectedAgent =
    agents.find((agent) => agent.agent_id === selectedAgentId) || null;

  const handleSend = (command) => {
    if (!selectedAgentId) return false;
    return sendCommand(selectedAgentId, command);
  };

  const agentTerminalOutput = selectedAgentId
    ? terminalOutput.filter(
        (entry) => !entry.agent_id || entry.agent_id === selectedAgentId
      )
    : terminalOutput;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur sticky top-0 z-10">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">ChimeraC2</h1>
          <p className="text-xs text-slate-400">Mission Control</p>
        </div>
        <ConnectionStatus status={status} />
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6">
        <AgentTable
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
        />

        <TerminalConsole
          output={agentTerminalOutput}
          selectedAgent={selectedAgent}
          onSend={handleSend}
        />
      </main>
    </div>
  );
}

function ConnectionStatus({ status }) {
  const color =
    status === 'open'
      ? 'bg-emerald-400 shadow-emerald-400/50'
      : status === 'connecting'
      ? 'bg-yellow-400 shadow-yellow-400/50 animate-pulse'
      : 'bg-red-400 shadow-red-400/50';

  const label =
    status === 'open'
      ? 'Connected'
      : status === 'connecting'
      ? 'Connecting…'
      : 'Disconnected';

  return (
    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300">
      <span className={`h-2 w-2 rounded-full shadow-sm ${color}`} />
      <span className="font-medium">{label}</span>
    </div>
  );
}
