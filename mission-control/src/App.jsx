import { useState } from 'react';
import AgentTable from './components/AgentTable';
import TerminalConsole from './components/TerminalConsole';

const dummyAgents = [
  {
    agent_id: 'AG-001',
    hostname: 'LAB-WIN11',
    os: 'Windows 11',
    user: 'student',
    is_privileged: false,
    ip: '192.168.1.101'
  },
  {
    agent_id: 'AG-002',
    hostname: 'LAB-LINUX',
    os: 'Ubuntu Linux',
    user: 'admin',
    is_privileged: true,
    ip: '192.168.1.102'
  },
  {
    agent_id: 'AG-003',
    hostname: 'LAB-TEST',
    os: 'Windows 10',
    user: 'tester',
    is_privileged: false,
    ip: '192.168.1.103'
  }
];

function App() {
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [outputs, setOutputs] = useState([]);

  const handleExecuteCommand = (agentId, command) => {
    setOutputs((previous) => [
      ...previous,
      {
        command,
        output: `Dummy response from ${agentId}`
      }
    ]);
  };

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <h1 className="text-2xl font-bold text-white mb-6">
        ChimeraC2 Mission Control
      </h1>

      <AgentTable
        agents={dummyAgents}
        selectedAgentId={selectedAgentId}
        onSelectAgent={setSelectedAgentId}
      />

      <TerminalConsole
        selectedAgentId={selectedAgentId}
        outputs={outputs}
        onExecuteCommand={handleExecuteCommand}
      />
    </main>
  );
}

export default App;