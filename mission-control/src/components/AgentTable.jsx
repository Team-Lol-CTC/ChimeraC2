import { Cpu, Radio, ShieldAlert, Server } from 'lucide-react';

export default function AgentTable({
  agents = [],
  selectedAgentId,
  onSelectAgent,
}) {
  return (
    <div className="group/card relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900/90 to-slate-950 shadow-2xl shadow-black/40 ring-1 ring-white/5">
      {/* Ambient top glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-24 h-48 bg-gradient-to-b from-indigo-500/20 via-indigo-500/5 to-transparent blur-2xl"
      />

      {/* Header */}
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

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 text-[11px] font-medium uppercase tracking-wider text-slate-400">
              <th className="px-6 py-3 font-medium">Agent ID</th>
              <th className="px-6 py-3 font-medium">Hostname</th>
              <th className="px-6 py-3 font-medium">Operating System</th>
              <th className="px-6 py-3 font-medium">User / Role</th>
              <th className="px-6 py-3 font-medium">Internal IP</th>
              <th className="px-6 py-3 text-right font-medium">Action</th>
            </tr>
          </thead>

          <tbody>
            {agents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-16 text-center">
                  <div className="mx-auto flex max-w-sm flex-col items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/5 ring-1 ring-inset ring-white/10">
                      <Radio
                        className="h-5 w-5 animate-pulse text-slate-400"
                        aria-hidden
                      />
                    </div>

                    <div>
                      <p className="text-sm font-medium text-slate-300">
                        No beacons connected
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
                const isSelected = agent.agent_id === selectedAgentId;
                const userLabel = agent.user || agent.current_user;

                return (
                  <tr
                    key={agent.agent_id}
                    className={`group relative border-b border-white/[0.06] transition-colors duration-200 last:border-b-0 ${
                      isSelected
                        ? 'bg-indigo-500/10'
                        : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    {/* Agent ID */}
                    <td className="relative px-6 py-4 font-mono text-sm font-semibold text-indigo-300">
                      <span
                        aria-hidden
                        className={`absolute inset-y-0 left-0 w-0.5 bg-gradient-to-b from-indigo-400 to-violet-500 transition-opacity duration-200 ${
                          isSelected ? 'opacity-100' : 'opacity-0'
                        }`}
                      />

                      {agent.agent_id}
                    </td>

                    {/* Hostname */}
                    <td className="px-6 py-4 font-medium text-white">
                      {agent.hostname}
                    </td>

                    {/* Operating System */}
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 font-mono text-xs text-sky-300">
                        <Cpu className="h-3 w-3" aria-hidden />
                        {agent.os}
                      </span>
                    </td>

                    {/* User */}
                    <td className="px-6 py-4">
                      {agent.is_privileged ? (
                        <span className="inline-flex items-center gap-1.5 rounded-md border border-rose-400/30 bg-rose-500/10 px-2.5 py-1 text-xs font-semibold text-rose-300">
                          <ShieldAlert
                            className="h-3 w-3"
                            aria-hidden
                          />
                          {userLabel}
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-medium text-slate-300">
                          {userLabel}
                        </span>
                      )}
                    </td>

                    {/* IP */}
                    <td className="px-6 py-4 font-mono text-sm text-slate-400">
                      {agent.ip || agent.internal_ip}
                    </td>

                    {/* Action */}
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => onSelectAgent?.(agent.agent_id)}
                        className={`inline-flex items-center justify-center rounded-lg px-4 py-1.5 text-xs font-semibold tracking-wide transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
                          isSelected
                            ? 'bg-gradient-to-b from-indigo-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                            : 'border border-white/10 bg-white/5 text-slate-200 hover:border-white/20 hover:bg-white/10 hover:text-white active:scale-95'
                        }`}
                      >
                        {isSelected ? 'Selected' : 'Interact'}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}