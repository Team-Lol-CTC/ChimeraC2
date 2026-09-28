import { useState } from "react"
import AgentTable from "./components/AgentTable"
import TerminalConsole from "./components/TerminalConsole"

const SAMPLE_AGENTS = [
  {
    agent_id: "AG-001",
    hostname: "WIN-DC01",
    os: "windows",
    user: "SYSTEM",
    ip: "10.0.12.4",
    last_check_in: "2026-09-28T00:30:00Z",
    status: "online",
  },
  {
    agent_id: "AG-002",
    hostname: "ubuntu-web-03",
    os: "linux",
    user: "www-data",
    ip: "10.0.12.51",
    last_check_in: "2026-09-28T00:28:00Z",
    status: "online",
  },
  {
    agent_id: "AG-003",
    hostname: "MACBOOK-PRO",
    os: "darwin",
    user: "j.reyes",
    ip: "10.0.12.88",
    last_check_in: "2026-09-28T00:20:00Z",
    status: "offline",
  },
]

function App() {
  const [selectedAgentId, setSelectedAgentId] = useState(null)
  const [output, setOutput] = useState([])

  const selectedAgent =
    SAMPLE_AGENTS.find(
      (agent) => agent.agent_id === selectedAgentId
    ) || null

  const handleSend = (command) => {
    if (!selectedAgent) {
      return false
    }

    const taskId = `TASK-${Date.now()}`

    
    setOutput((previous) => [
      ...previous,
      {
        kind: "queued",
        task_id: taskId,
        agent_id: selectedAgent.agent_id,
        command,
        ts: new Date().toISOString(),
      },
    ])

    
    setTimeout(() => {
      const dummyResponse = `Response from ${selectedAgent.agent_id}\nCommand: ${command}`

      const encodedOutput = btoa(dummyResponse)

      setOutput((previous) => [
        ...previous,
        {
          kind: "result",
          task_id: taskId,
          agent_id: selectedAgent.agent_id,
          output: encodedOutput,
          exit_code: 0,
          ts: new Date().toISOString(),
        },
      ])
    }, 500)

    return true
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <h1 className="mb-6 text-2xl font-bold text-white">
        ChimeraC2 Mission Control
      </h1>

      <div className="space-y-6">
        <AgentTable
          agents={SAMPLE_AGENTS}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
        />

        <TerminalConsole
          output={output}
          selectedAgent={selectedAgent}
          onSend={handleSend}
        />
      </div>
    </main>
  )
}

export default App