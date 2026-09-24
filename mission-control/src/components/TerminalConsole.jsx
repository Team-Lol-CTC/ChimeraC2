import { useState } from 'react';

export default function TerminalConsole({
  selectedAgentId,
  outputs = [],
  onExecuteCommand
}) {
  const [commandInput, setCommandInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!commandInput.trim() || !selectedAgentId) return;

    onExecuteCommand(selectedAgentId, commandInput.trim());
    setCommandInput('');
  };

  return (
    <div className="bg-black border border-slate-800 rounded-lg p-4 font-mono shadow-2xl">
      <div className="flex justify-between items-center pb-2 mb-3 border-b border-slate-800 text-xs">
        <span className="text-slate-400 font-bold uppercase tracking-wider">
          Terminal Session:{' '}
          <span className="text-emerald-400">
            {selectedAgentId
              ? `Agent [${selectedAgentId}]`
              : 'Select an Agent Above'}
          </span>
        </span>

        <span className="text-[11px] text-slate-600">
          Interactive Shell / WebSockets
        </span>
      </div>

      <div className="h-60 overflow-y-auto space-y-2 text-xs mb-3 pr-2 scrollbar-thin scrollbar-thumb-slate-800">
        {outputs.length === 0 ? (
          <p className="text-slate-600 italic">
            Awaiting task dispatches and execution returns...
          </p>
        ) : (
          outputs.map((entry, index) => (
            <div key={index} className="space-y-1">
              <p className="text-sky-400 font-bold">
                &gt; {entry.command}
              </p>

              <pre className="text-slate-300 whitespace-pre-wrap bg-slate-950 p-2 rounded border border-slate-900">
                {entry.output || '[No output returned]'}
              </pre>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={commandInput}
          disabled={!selectedAgentId}
          onChange={(e) => setCommandInput(e.target.value)}
          placeholder={
            selectedAgentId
              ? 'Type shell command...'
              : 'Select an agent to issue commands'
          }
          className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-emerald-300 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!selectedAgentId || !commandInput.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-bold px-4 py-2 rounded transition-colors"
        >
          Send Task
        </button>
      </form>
    </div>
  );
}