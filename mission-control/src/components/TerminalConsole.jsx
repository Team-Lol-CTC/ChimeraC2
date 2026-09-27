// MOCK — Saliha will replace this with the real TerminalConsole.
// Props contract:
//   output:        TerminalEntry[]
//   selectedAgent: Agent | null
//   onSend:        (command: string) => boolean

import { useState, useRef, useEffect } from 'react';

export default function TerminalConsole({
  output = [],
  selectedAgent = null,
  onSend = () => false,
}) {
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || !selectedAgent) return;
    onSend(input.trim());
    setInput('');
  };

  if (!selectedAgent) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500">
        Select an agent to open a terminal.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div
        ref={scrollRef}
        className="flex-1 overflow-auto p-4 font-mono text-xs space-y-1 bg-gray-950"
      >
        {output.length === 0 && (
          <div className="text-gray-600">
            Terminal ready — type a command below.
          </div>
        )}
        {output.map((entry, i) => (
          <div key={i}>
            {entry.kind === 'queued' && (
              <div className="text-yellow-400">
                $ {entry.command}{' '}
                <span className="text-gray-600">[queued]</span>
              </div>
            )}
            {entry.kind === 'result' && (
              <div className="text-gray-300">
                {entry.output
                  ? atob(entry.output)
                  : '(no output)'}
                <span className="text-gray-600 ml-2">
                  [exit {entry.exit_code}]
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-800 flex items-center"
      >
        <span className="pl-4 text-green-500 font-mono text-xs">$</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="type a command…"
          className="flex-1 bg-transparent px-3 py-3 text-sm font-mono text-gray-100 outline-none placeholder-gray-600"
          autoFocus
        />
        <button
          type="submit"
          className="px-4 py-3 text-xs text-gray-400 hover:text-gray-100 transition-colors"
        >
          ↵ send
        </button>
      </form>
    </div>
  );
}
