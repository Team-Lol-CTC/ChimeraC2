import { Cpu, Radio, Server } from "lucide-react"

export default function AgentTable({
  agents = [],
  selectedAgentId,
  onSelectAgent,
}) {
  return (
    <div className="group/card relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900/90 to-slate-950 shadow-2xl shadow-black/40 ring-1 ring-white/5">
      
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-24 h-48 bg-gradient-to-b from-indigo-500/20 via-indigo-500/5 to-transparent blur-2xl"
      />

      
      <div className="relative flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-500/5 ring-1 ring-inset ring-indigo-400/20">
            <Server className="h-5 w-5 text-indigo-300" aria-hidden />
          </div>

          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold tracking-tight text-white">
              Active Target Fleet
              <span className="inline-flex items-center rounded-full bg-white/5 px-2 py-0.5 text-xs font-medium text-slate-300 ring-1 ring-inset ring-white/10">
                {agents.length}
              </span>
            </h2>

            <p className="mt-0.5 text-xs text-slate-400">
              Live beacon telemetry &amp; agent orchestration
            </p>
          </div>
        </div>

        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          Real-Time Telemetry
        </span>
      </div>

      
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 bg-gray-950 text-[11px] font-medium uppercase tracking-wider text-gray-400">
              <th className="px-6 py-3 font-medium">Agent ID</th>
              <th className="px-6 py-3 font-medium">Hostname</th>
              <th className="px-6 py-3 font-medium">Operating System</th>
              <th className="px-6 py-3 font-medium">User</th>
              <th className="px-6 py-3 font-medium">Internal IP</th>
              <th className="px-6 py-3 font-medium">Last Check-In</th>
              <th className="px-6 py-3 text-right font-medium">Action</th>
            </tr>
          </thead>

          <tbody>
            {agents.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-16 text-center">
                  <div className="mx-auto flex max-w-sm flex-col items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/5 ring-1 ring-inset ring-white/10">
                      <Radio
                        className="h-5 w-5 animate-pulse text-slate-400"
                        aria-hidden
                      />
                    </div>

                    <div>
                      <p className="text-sm font-medium text-slate-300">
                        No agents connected
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Waiting for agent check-in&hellip;
                      </p>
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              agents.map((agent) => {
                const isSelected = agent.agent_id === selectedAgentId
                const isOnline = agent.status === "online"

                let osBadgeClass =
                  "border-purple-400/20 bg-purple-500/10 text-purple-300"

                if (agent.os === "linux") {
                  osBadgeClass =
                    "border-yellow-400/20 bg-yellow-500/10 text-yellow-300"
                } else if (agent.os === "windows") {
                  osBadgeClass =
                    "border-blue-400/20 bg-blue-500/10 text-blue-300"
                }

                return (
                  <tr
                    key={agent.agent_id}
                    onClick={() => onSelectAgent(agent.agent_id)}
                    className={`group cursor-pointer border-t border-gray-800 transition-colors duration-200 ${
                      isSelected
                        ? "bg-gray-800"
                        : "hover:bg-gray-900/80"
                    }`}
                  >
                   
                    <td className="px-6 py-4 font-mono text-sm font-semibold text-indigo-300">
                      {agent.agent_id}
                    </td>

                  
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span
                          className={`h-2.5 w-2.5 rounded-full ${
                            isOnline
                              ? "bg-emerald-400 shadow-lg shadow-emerald-400/40"
                              : "bg-red-400 shadow-lg shadow-red-400/30"
                          }`}
                        />

                        <span className="font-medium text-white">
                          {agent.hostname}
                        </span>
                      </div>
                    </td>

                  
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 font-mono text-xs ${osBadgeClass}`}
                      >
                        <Cpu className="h-3 w-3" aria-hidden />
                        {agent.os}
                      </span>
                    </td>

                  
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {agent.user}
                    </td>

                    <td className="px-6 py-4 font-mono text-sm text-slate-400">
                      {agent.ip}
                    </td>

               
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {agent.last_check_in
                        ? new Date(agent.last_check_in).toLocaleString()
                        : "Never"}
                    </td>

                
                    <td className="px-6 py-4 text-right">
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation()
                          onSelectAgent(agent.agent_id)
                        }}
                        className={`inline-flex items-center justify-center rounded-lg px-4 py-1.5 text-xs font-semibold tracking-wide transition-all duration-200 ${
                          isSelected
                            ? "bg-gradient-to-b from-indigo-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/25"
                            : "border border-white/10 bg-white/5 text-slate-200 hover:border-white/20 hover:bg-white/10 hover:text-white active:scale-95"
                        }`}
                      >
                        {isSelected ? "Selected" : "Interact"}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}