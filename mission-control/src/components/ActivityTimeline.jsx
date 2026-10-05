import { useCallback, useEffect, useState } from 'react';

const API_URL = 'http://127.0.0.1:8000';

const EVENT_STYLES = {
  AGENT_REGISTERED: {
    icon: '●',
    label: 'Agent Registered',
    className: 'text-emerald-400',
  },
  AGENT_ONLINE: {
    icon: '↑',
    label: 'Agent Online',
    className: 'text-emerald-400',
  },
  AGENT_OFFLINE: {
    icon: '↓',
    label: 'Agent Offline',
    className: 'text-red-400',
  },
  TASK_CREATED: {
    icon: '+',
    label: 'Task Created',
    className: 'text-blue-400',
  },
  TASK_RUNNING: {
    icon: '▶',
    label: 'Task Running',
    className: 'text-yellow-400',
  },
  TASK_COMPLETED: {
    icon: '✓',
    label: 'Task Completed',
    className: 'text-emerald-400',
  },
  TASK_FAILED: {
    icon: '!',
    label: 'Task Failed',
    className: 'text-red-400',
  },
};

function formatTime(timestamp) {
  if (!timestamp) return 'Unknown';

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString();
}

function getEventStyle(eventType) {
  return (
    EVENT_STYLES[eventType] || {
      icon: '•',
      label: eventType || 'Unknown Event',
      className: 'text-slate-400',
    }
  );
}

export default function ActivityTimeline({ selectedAgentId }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadLogs = useCallback(async () => {
    try {
      setError('');

      const params = new URLSearchParams();

      if (selectedAgentId) {
        params.set('agent_id', selectedAgentId);
      }

      params.set('limit', '100');

      const response = await fetch(
        `${API_URL}/api/v1/audit?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const data = await response.json();

      setLogs(
        Array.isArray(data.logs)
          ? data.logs
          : []
      );
    } catch (err) {
      setError(
        err.message || 'Failed to load activity'
      );
    } finally {
      setLoading(false);
    }
  }, [selectedAgentId]);

  useEffect(() => {
    loadLogs();

    const interval = setInterval(
      loadLogs,
      3000
    );

    return () => {
      clearInterval(interval);
    };
  }, [loadLogs]);

  return (
    <section className="rounded-2xl border border-white/10 bg-slate-900/70 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Activity Timeline
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Recent agent and task events
          </p>
        </div>

        <button
          onClick={loadLogs}
          disabled={loading}
          className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/10 disabled:opacity-50"
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {/* Content */}
      <div className="max-h-[420px] overflow-y-auto">
        {loading && logs.length === 0 && (
          <div className="px-5 py-10 text-center text-sm text-slate-500">
            Loading activity…
          </div>
        )}

        {!loading && error && (
          <div className="px-5 py-10 text-center">
            <p className="text-sm text-red-400">
              {error}
            </p>

            <button
              onClick={loadLogs}
              className="mt-3 text-xs text-slate-400 underline hover:text-white"
            >
              Try again
            </button>
          </div>
        )}

        {!loading &&
          !error &&
          logs.length === 0 && (
            <div className="px-5 py-10 text-center text-sm text-slate-500">
              No activity recorded yet.
            </div>
          )}

        {logs.map((log) => {
          const event = getEventStyle(
            log.event_type
          );

          return (
            <div
              key={log.id}
              className="border-b border-white/5 px-5 py-4 last:border-b-0 hover:bg-white/[0.02]"
            >
              <div className="flex gap-4">
                {/* Event icon */}
                <div
                  className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-bold ${event.className}`}
                >
                  {event.icon}
                </div>

                {/* Event details */}
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-xs font-semibold ${event.className}`}
                    >
                      {event.label}
                    </span>

                    <span className="text-[10px] text-slate-600">
                      {formatTime(
                        log.created_at
                      )}
                    </span>
                  </div>

                  <p className="mt-1 text-sm text-slate-300">
                    {log.message}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2">
                    {log.agent_id && (
                      <span className="rounded-md border border-white/10 bg-black/20 px-2 py-1 font-mono text-[10px] text-slate-500">
                        agent:{' '}
                        {log.agent_id}
                      </span>
                    )}

                    {log.task_id && (
                      <span className="rounded-md border border-white/10 bg-black/20 px-2 py-1 font-mono text-[10px] text-slate-500">
                        task:{' '}
                        {log.task_id}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}