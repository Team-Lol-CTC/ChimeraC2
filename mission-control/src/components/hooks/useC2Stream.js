import { useState, useEffect, useRef } from 'react';

export function useC2Stream(wsUrl = 'ws://localhost:8000/ws/operator') {
  const [agents, setAgents] = useState([]);
  const [terminalOutput, setTerminalOutput] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'AGENT_REGISTER') {
        setAgents((prev) => [
          ...prev.filter((a) => a.agent_id !== data.agent.agent_id),
          data.agent,
        ]);
      } else if (data.type === 'TASK_RESULT') {
        setTerminalOutput((prev) => [...prev, data]);
      }
    };

    return () => ws.close();
  }, [wsUrl]);

  const sendCommand = (agentId, command) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({ action: 'exec', agent_id: agentId, command })
      );
    }
  };

  return { agents, terminalOutput, sendCommand };
}
