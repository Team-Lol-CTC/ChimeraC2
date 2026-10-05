import { useEffect, useRef, useState } from "react"

export default function TerminalConsole({
  output = [],
  selectedAgent,
  onSend,
}) {
  const [command, setCommand] = useState("")
  const outputRef = useRef(null)

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  const handleSubmit = (event) => {
    event.preventDefault()

    const trimmedCommand = command.trim()

    if (!trimmedCommand || !selectedAgent) {
      return
    }

    const sent = onSend(trimmedCommand)

    if (sent) {
      setCommand("")
    }
  }

  const decodeOutput = (output) => {
    if (!output) {
      return ""
    }

    return output
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950 shadow-2xl shadow-black/40 ring-1 ring-white/5">
      <div className="flex items-center justify-between border-b border-gray-800 bg-gray-950 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Terminal Console
          </h2>

          <p className="mt-1 text-xs text-gray-500">
            {selectedAgent
              ? `Connected to ${selectedAgent.hostname}`
              : "No agent selected"}
          </p>
        </div>

        {selectedAgent && (
          <span className="rounded-md border border-emerald-400/20 bg-emerald-500/10 px-2.5 py-1 font-mono text-xs text-emerald-300">
            {selectedAgent.agent_id}
          </span>
        )}
      </div>

      <div
        ref={outputRef}
        className="h-80 overflow-y-auto bg-gray-950 p-4 font-mono text-xs"
      >
        {!selectedAgent ? (
          <div className="flex h-full items-center justify-center text-gray-500">
            Select an agent to open a terminal.
          </div>
        ) : output.length === 0 ? (
          <div className="text-gray-500">
            No terminal activity yet.
          </div>
        ) : (
          <div className="space-y-2">
            {output.map((entry) => {
              if (entry.kind === "queued") {
                return (
                  <div
                    key={`${entry.task_id}-queued`}
                    className="text-yellow-400"
                  >
                    <span className="text-gray-600">
                      [{entry.ts}]
                    </span>{" "}
                    $ {entry.command}
                  </div>
                )
              }

              if (entry.kind === "result") {
                return (
                  <div
                    key={`${entry.task_id}-result`}
                    className="text-gray-300"
                  >
                    <div className="mb-1 text-gray-600">
                      [{entry.ts}]
                    </div>

                    <pre className="whitespace-pre-wrap break-words">
                      {decodeOutput(entry.output)}
                    </pre>

                    <div className="mt-1 text-gray-500">
                      [exit {entry.exit_code ?? 0}]
                    </div>
                  </div>
                )
              }

              return null
            })}
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex items-center border-t border-gray-800 bg-transparent"
      >
        <span className="px-4 font-mono text-sm text-emerald-400">
          $
        </span>

        <input
          type="text"
          value={command}
          onChange={(event) => setCommand(event.target.value)}
          disabled={!selectedAgent}
          placeholder={
            selectedAgent
              ? "Enter command..."
              : "Select an agent first"
          }
          className="min-w-0 flex-1 bg-transparent py-4 pr-4 font-mono text-sm text-gray-200 outline-none placeholder:text-gray-600 disabled:cursor-not-allowed"
        />

        <button
          type="submit"
          disabled={!selectedAgent || !command.trim()}
          className="mr-3 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-gray-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  )
}
