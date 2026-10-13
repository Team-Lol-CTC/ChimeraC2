
import {
  Cpu,
  MemoryStick,
  Monitor,
  UserRound,
  ShieldCheck,
  Activity,
  Network,
  Server,
  ListTree,
} from "lucide-react";

export default function TriageDetails({ selectedAgent }) {
  if (!selectedAgent) {
    return (
      <section className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-950 p-8 text-slate-100">
        <div className="flex min-h-48 flex-col items-center justify-center text-center">
          <div className="mb-4 rounded-2xl border border-white/10 bg-white/5 p-4">
            <Activity className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-lg font-semibold">System Triage</h2>
          <p className="mt-2 max-w-sm text-sm text-slate-400">
            Select an agent from the fleet table to inspect its system
            information and running processes.
          </p>
        </div>
      </section>
    );
  }

  const totalRam = selectedAgent.total_ram_gb;
  const availableRam = selectedAgent.available_ram_gb;
  const ramValuesAvailable =
    typeof totalRam === "number" &&
    typeof availableRam === "number" &&
    totalRam > 0;

  const usedRam = ramValuesAvailable
    ? Math.max(0, totalRam - availableRam)
    : null;

  const ramUsage = ramValuesAvailable
    ? Math.min(100, Math.max(0, (usedRam / totalRam) * 100))
    : null;

  const processes = Array.isArray(selectedAgent.sample_processes)
    ? selectedAgent.sample_processes
    : [];

  const systemInfo = [
    {
      label: "Operating System",
      value: [selectedAgent.os, selectedAgent.os_release]
        .filter(Boolean)
        .join(" ") || "Unavailable",
      icon: Monitor,
    },
    {
      label: "Architecture",
      value: selectedAgent.architecture || "Unavailable",
      icon: Server,
    },
    {
      label: "User",
      value: selectedAgent.user || "Unavailable",
      icon: UserRound,
    },
    {
      label: "Privileges",
      value:
        typeof selectedAgent.is_privileged === "boolean"
          ? selectedAgent.is_privileged
            ? "Privileged"
            : "Standard user"
          : "Unavailable",
      icon: ShieldCheck,
    },
    {
      label: "IP Address",
      value: selectedAgent.ip || "Unavailable",
      icon: Network,
    },
  ];

  return (
    <section className="space-y-5 rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-950 p-5 text-slate-100 sm:p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3">
            <Activity className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">
              System Triage
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Detailed information for the selected agent
            </p>
          </div>
        </div>

        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300">
          {selectedAgent.status || "Status unavailable"}
        </span>
      </div>

      {/* Selected agent */}
      <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <div className="rounded-lg bg-indigo-400/10 p-2.5">
          <Monitor className="h-5 w-5 text-indigo-300" />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium text-white">
            {selectedAgent.hostname || "Unknown host"}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Agent ID: {selectedAgent.agent_id}
          </p>
        </div>
      </div>

      {/* Main metrics */}
      <div className="grid gap-4 sm:grid-cols-2">
        <MetricCard
          icon={Cpu}
          label="CPU Cores"
          value={selectedAgent.cpu_cores ?? "—"}
          detail="Logical processor cores"
          accent="text-indigo-300"
        />

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <div className="flex items-center gap-2">
            <MemoryStick className="h-4 w-4 text-cyan-300" />
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Memory
            </span>
          </div>

          <p className="mt-3 text-2xl font-semibold tracking-tight text-white">
            {ramValuesAvailable ? `${usedRam.toFixed(1)} GB` : "—"}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {ramValuesAvailable
              ? `Available: ${availableRam.toFixed(1)} GB of ${totalRam.toFixed(1)} GB`
              : "Memory data unavailable"}
          </p>

          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-700/70">
            <div
              className="h-full rounded-full bg-cyan-400 transition-all"
              style={{ width: `${ramUsage ?? 0}%` }}
            />
          </div>
          <p className="mt-2 text-right text-xs text-slate-500">
            {ramUsage === null ? "—" : `${ramUsage.toFixed(0)}% used`}
          </p>
        </div>
      </div>

      {/* System details */}
      <div className="overflow-hidden rounded-xl border border-white/10">
        <div className="flex items-center gap-2 border-b border-white/10 bg-white/[0.03] px-4 py-3">
          <Monitor className="h-4 w-4 text-slate-400" />
          <h3 className="text-sm font-semibold">System Information</h3>
        </div>

        <div className="divide-y divide-white/5">
          {systemInfo.map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
            >
              <span className="flex items-center gap-2 text-sm text-slate-400">
                <Icon className="h-4 w-4" />
                {label}
              </span>
              <span className="max-w-full break-all text-right text-sm text-slate-200">
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Processes */}
      <div className="overflow-hidden rounded-xl border border-white/10">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-white/[0.03] px-4 py-3">
          <div className="flex items-center gap-2">
            <ListTree className="h-4 w-4 text-emerald-400" />
            <h3 className="text-sm font-semibold">Running Processes</h3>
          </div>
          <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs text-slate-400">
            {processes.length} listed
          </span>
        </div>

        {processes.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-64 text-left text-sm">
              <thead className="bg-white/[0.02] text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">PID</th>
                  <th className="px-4 py-3 font-medium">Process Name</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {processes.map((process, index) => (
                  <tr
                    key={process.pid ?? `${process.name}-${index}`}
                    className="transition-colors hover:bg-white/[0.03]"
                  >
                    <td className="px-4 py-3 font-mono text-slate-400">
                      {process.pid ?? "—"}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-200">
                      {process.name || "Unknown process"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-4 py-8 text-center">
            <ListTree className="mx-auto mb-2 h-6 w-6 text-slate-600" />
            <p className="text-sm text-slate-400">
              No process information available
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Process details will appear when the agent reports them.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

function MetricCard({ icon: Icon, label, value, detail, accent }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${accent}`} />
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {label}
        </span>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-white">
        {value}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}