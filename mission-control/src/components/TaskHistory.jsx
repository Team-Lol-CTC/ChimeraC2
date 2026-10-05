import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Clock3, RefreshCw, XCircle } from "lucide-react"

const API_URL = "http://127.0.0.1:8000"

export default function TaskHistory({ selectedAgentId }) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadTasks = useCallback(async () => {
    setLoading(true)
    setError("")

    try {
      const url = selectedAgentId
        ? `${API_URL}/api/v1/tasks?agent_id=${encodeURIComponent(selectedAgentId)}`
        : `${API_URL}/api/v1/tasks`

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      setTasks(Array.isArray(data.tasks) ? data.tasks : [])
    } catch (err) {
      console.error("[TaskHistory]", err)
      setError("Unable to load task history.")
    } finally {
      setLoading(false)
    }
  }, [selectedAgentId])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900/90 to-slate-950 shadow-2xl shadow-black/40 ring-1 ring-white/5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-6 py-5">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-white">
            Task History
          </h2>

          <p className="mt-0.5 text-xs text-slate-400">
            Persisted task execution history
          </p>
        </div>

        <button
          type="button"
          onClick={loadTasks}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${
              loading ? "animate-spin" : ""
            }`}
          />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="border-b border-red-400/10 bg-red-400/5 px-6 py-4 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && tasks.length === 0 ? (
        <div className="px-6 py-12 text-center text-xs text-slate-500">
          Loading task history…
        </div>
      ) : tasks.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <Clock3 className="mx-auto h-6 w-6 text-slate-500" />

          <p className="mt-3 text-sm text-slate-300">
            No task history
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Completed tasks will appear here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-gray-950 text-[11px] font-medium uppercase tracking-wider text-gray-400">
                <th className="px-6 py-3">Task ID</th>
                <th className="px-6 py-3">Agent</th>
                <th className="px-6 py-3">Command</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Exit</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3">Completed</th>
              </tr>
            </thead>

            <tbody>
              {tasks.map((task) => (
                <tr
                  key={task.task_id}
                  className="border-t border-gray-800 hover:bg-gray-900/70"
                >
                  <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-indigo-300">
                    {task.task_id}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-slate-400">
                    {task.agent_id}
                  </td>

                  <td className="max-w-md px-6 py-4">
                    <code className="block truncate font-mono text-xs text-slate-200">
                      {task.command}
                    </code>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4">
                    <StatusBadge status={task.status} />
                  </td>

                  <td className="px-6 py-4 font-mono text-xs text-slate-400">
                    {task.exit_code}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">
                    {formatDate(task.created_at)}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">
                    {formatDate(task.completed_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}


function StatusBadge({ status }) {
  const normalized = status?.toUpperCase()

  if (normalized === "COMPLETED") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-300">
        <CheckCircle2 className="h-3 w-3" />
        COMPLETED
      </span>
    )
  }

  if (normalized === "RUNNING") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-yellow-400/20 bg-yellow-400/10 px-2.5 py-1 text-[11px] font-semibold text-yellow-300">
        <Clock3 className="h-3 w-3" />
        RUNNING
      </span>
    )
  }

  if (normalized === "FAILED") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-red-400/20 bg-red-400/10 px-2.5 py-1 text-[11px] font-semibold text-red-300">
        <XCircle className="h-3 w-3" />
        FAILED
      </span>
    )
  }

  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
      {normalized || "UNKNOWN"}
    </span>
  )
}


function formatDate(value) {
  if (!value) {
    return "—"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}